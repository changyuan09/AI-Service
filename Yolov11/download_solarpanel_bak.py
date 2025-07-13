import os
import json
import math
import requests
from io import BytesIO
from PIL import Image
from shapely.geometry import Polygon, box
from shapely.geometry import box, mapping
from pyproj import CRS, Transformer
import mercantile
import rasterio
from rasterio import mask
from rasterio.merge import merge
from rasterio.transform import from_origin
import tempfile
import numpy as np
from shapely.ops import transform
from shapely import wkb
from pg_conn import get_grids, update_grid_status, insert_solar_panel, get_countrys
from yolo_predict import predict
import time
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
import concurrent.futures
from tqdm import tqdm
import argparse

ZOOM_LEVEL = 21
BUFFER_DISTANCE = 50
BUFFER_DISTANCE2 = 40
EPSG_3857 = "EPSG:3857"
EPSG_4326 = "EPSG:4326"
YOLO_IMAGE_SIZE = 640
MAX_WORKERS = 16

disable_warnings(InsecureRequestWarning)


def latlon_to_mercator(lat, lon):
    transformer = Transformer.from_crs(EPSG_4326, EPSG_3857, always_xy=True)
    return transformer.transform(lon, lat)


def mercator_to_latlon(x, y):
    transformer = Transformer.from_crs(EPSG_3857, EPSG_4326, always_xy=True)
    return transformer.transform(x, y)


def get_google_tile_url(x, y, z):
    return f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"


def download_tile(url):
    max_retries = 500
    for attempt in range(max_retries):
        try:
            response = requests.get(url, verify=False)
            response.raise_for_status()

            return Image.open(BytesIO(response.content))
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(2)

    raise Exception(f"Failed to download tile after {max_retries} attempts: {url}")


def get_tiles_in_bbox(bbox, zoom):
    west, south, east, north = bbox
    tiles = mercantile.tiles(west, south, east, north, zoom)
    return list(tiles)


def reproject_geometry(geom, source_crs, target_crs):
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return transform(transformer.transform, geom)


def check_geometry_overlap(raster_bbox, geometry):
    raster_geom = box(*raster_bbox)
    return raster_geom.intersects(geometry)


def get_yolo_image(image):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image_resized = image.resize((YOLO_IMAGE_SIZE, YOLO_IMAGE_SIZE), Image.LANCZOS)
    return image_resized


def download_and_save_tile(tile, i, temp_dir, zoom):
    try:
        tile_url = get_google_tile_url(tile.x, tile.y, zoom)
        img = download_tile(tile_url)

        img_array = np.array(img)
        if len(img_array.shape) == 2:
            img_array = np.stack([img_array] * 3, axis=-1)

        temp_file = os.path.join(temp_dir, f"tile_{i}.tif")
        tile_bbox = mercantile.bounds(tile)

        transform = from_origin(
            tile_bbox.west,
            tile_bbox.north,
            (tile_bbox.east - tile_bbox.west) / 256,
            (tile_bbox.north - tile_bbox.south) / 256,
        )

        with rasterio.open(
            temp_file,
            "w",
            driver="GTiff",
            height=img_array.shape[0],
            width=img_array.shape[1],
            count=3,
            dtype=img_array.dtype,
            crs=EPSG_3857,
            transform=transform,
        ) as dst:
            for band in range(3):
                dst.write(img_array[:, :, band], band + 1)

        return temp_file
    except Exception as e:
        print(f"failed to download tile {i}. exception: {e}")
        return None


def download_tiles_concurrently(tiles, temp_dir, zoom):
    temp_files = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_and_save_tile, tile, i, temp_dir, zoom): i for i, tile in enumerate(tiles)}

        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(tiles),
            desc="downloading tile",
        ):
            i = futures[future]
            try:
                temp_file = future.result()
                if temp_file:
                    temp_files.append(temp_file)
            except Exception as e:
                print(f"failed to download tile {i}. exception: {e}")

    return temp_files


def merge_tiles(tiles, zoom, output_path, buffer_polygon, grid_id):
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    size = len(tiles)
    if size == 0:
        print("does not have any tiles, cannot merge.")
        update_grid_status(grid_id, False)
        return
    temp_files = download_tiles_concurrently(tiles, temp_dir, zoom)

    if len(temp_files) != size:
        print(f"警告: 下载的瓦片数量与预期不符，预期 {size} 个瓦片，但实际下载了 {len(temp_files)} 个瓦片。")
        update_grid_status(grid_id, False)
        return

    src_files_to_mosaic = []
    for fp in temp_files:
        src = rasterio.open(fp)
        src_files_to_mosaic.append(src)

    try:
        mosaic, out_trans = merge(src_files_to_mosaic)

        merged_temp_file = os.path.join(temp_dir, "merged_temp.tif")

        out_meta = src.meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
                "crs": "EPSG:4326",
            }
        )

        with rasterio.open(merged_temp_file, "w", **out_meta) as dest:
            dest.write(mosaic)

        with rasterio.open(merged_temp_file) as src:
            raster_bbox = (
                src.bounds.left,
                src.bounds.bottom,
                src.bounds.right,
                src.bounds.top,
            )

            if not check_geometry_overlap(raster_bbox, buffer_polygon):
                raster_geom = box(*raster_bbox)
                intersection = raster_geom.intersection(buffer_polygon)

                if intersection.is_empty:
                    print("warning: polygon does not overlap with raster data, returning full raster")
                    out_image = mosaic
                    out_transform = out_trans
                else:
                    print("waring: polygon intersects with raster data, using intersection area")
                    geom = [mapping(intersection)]
                    out_image, out_transform = mask.mask(src, geom, crop=True)
            else:
                geom = [json.loads(json.dumps(buffer_polygon.__geo_interface__))]
                out_image, out_transform = mask.mask(src, geom, crop=True)

            out_meta = src.meta.copy()

        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "crs": EPSG_4326,
            }
        )
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)
        array = np.moveaxis(out_image, 0, -1)
        image = Image.fromarray(array)

    finally:
        for src in src_files_to_mosaic:
            src.close()
        for fp in temp_files + [merged_temp_file]:
            try:
                if os.path.exists(fp):
                    os.remove(fp)
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass
    return get_yolo_image(image)


def process_geojson(city_name, country_name, country_grid_name):
    grids = get_grids(country_grid_name)
    total_grids = len(grids)

    for index, grid in enumerate(grids, 1):
        hex_wkb = grid["geom"]
        geom = wkb.loads(bytes.fromhex(hex_wkb))
        id = grid["id"]
        is_deal = grid["is_deal"]

        if is_deal == True:
            print(f"Grid {id} has already been processed, skipping.")
            continue
        progress = f"[{index}/{total_grids}] {index/total_grids:.1%}"
        progress_bar = f"[{'#' * int(index/total_grids*20):<20}]"
        print(f"\n{progress} {progress_bar} processing grid ID: {id}")
        minx, miny, maxx, maxy = geom.bounds
        west, south = mercator_to_latlon(minx, miny)
        east, north = mercator_to_latlon(maxx, maxy)
        bbox = (west, south, east, north)
        tiles = get_tiles_in_bbox(bbox, ZOOM_LEVEL)
        if tiles:
            output_dir = f"output"
            os.makedirs(output_dir, exist_ok=True)
            epsg_3857_envelope = geom.envelope
            epsg_4326_envelope = reproject_geometry(epsg_3857_envelope, "EPSG:3857", "EPSG:4326")
            output_filename = os.path.join(output_dir, f"grid_{id}.tif")
            yolo_image = merge_tiles(tiles, ZOOM_LEVEL, output_filename, epsg_4326_envelope, id)
            if yolo_image is None:
                print(f"Failed to create YOLO image for grid {id}, skipping.")
                continue
            # yolo_image.save(output_filename2, format="JPEG", quality=100)
            scores, detect_boxs = predict(yolo_image, epsg_4326_envelope)
            if len(detect_boxs) > 0 and len(scores) > 0 and len(scores) == len(detect_boxs):
                insert_solar_panel(scores, detect_boxs, country_name, city_name, id)
            update_grid_status(id, True, country_grid_name)
        else:
            print(f"No tiles found for grid {id}")
            update_grid_status(id, False, country_grid_name)


if __name__ == "__main__":
    # country_name fro parameters

    parser = argparse.ArgumentParser(description="ai deal solar panel")
    parser.add_argument("--county_name", help="county name or zone name")
    args = parser.parse_args()
    countrys, city_name = get_countrys(args.county_name)
    for country in countrys:
        if country["is_deal"] == True:
            print(f"Country {country['name']} has already been processed, skipping.")
            continue
        print(f"---------------------------------------Processing country {country['name']} ------------------------------------------------ ")
        country_grid_name = f"{city_name}_{country['name']}_grid"
        # country_grid_name=f"{country['name']}_grid"
        process_geojson(city_name, country["name"], country_grid_name)
        print(f"---------------------------------------Finished processing country {country['name']} ------------------------------------------------ ")
