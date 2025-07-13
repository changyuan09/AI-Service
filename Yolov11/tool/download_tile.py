import os
import json
import math
import requests
from io import BytesIO
from PIL import Image
import geopandas as gpd
from shapely.geometry import Point, Polygon, box
from shapely.geometry import box, mapping
from pyproj import CRS, Transformer
import mercantile
import rasterio
from rasterio import mask 
from rasterio.merge import merge
from rasterio.transform import from_origin
import tempfile
import numpy as np
from pyproj import Geod
from functools import partial
from shapely.ops import transform
import argparse

ZOOM_LEVEL = 21  # 瓦片缩放级别
BUFFER_DISTANCE = 50  # 缓冲距离（米）
BUFFER_DISTANCE2 = 40  # 缓冲距离（米）
OUTPUT_CRS = "EPSG:3857"  # Web墨卡托投影，Google Maps使用的坐标系

def latlon_to_mercator(lat, lon):
    """将经纬度坐标转换为Web墨卡托投影坐标"""
    transformer = Transformer.from_crs("EPSG:4326", OUTPUT_CRS, always_xy=True)
    return transformer.transform(lon, lat)

def mercator_to_latlon(x, y):
    """将Web墨卡托投影坐标转换为经纬度坐标"""
    transformer = Transformer.from_crs(OUTPUT_CRS, "EPSG:4326", always_xy=True)
    return transformer.transform(x, y)

def get_google_tile_url(x, y, z):
    """获取Google地图瓦片URL"""
    return f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"

def download_tile(url):
    """下载瓦片图像"""
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        raise Exception(f"Failed to download tile: {url}")

def get_tiles_in_bbox(bbox, zoom):
    """获取边界框内的所有瓦片"""
    west, south, east, north = bbox
    tiles = mercantile.tiles(west, south, east, north, zoom)
    return list(tiles)

def geodesic_point_buffer(center_lon: float, center_lat: float, length_meters: float) -> tuple:
    """
    根据中心点和边长计算地理边界框（WGS84坐标系）
    
    参数:
        center_lon: 中心点经度 (度)
        center_lat: 中心点纬度 (度)
        length_meters: 边界框边长 (米)
        
    返回:
        (north, south, east, west) 边界坐标 (度)
    """
    EARTH_RADIUS = 6371000  # WGS84椭球体长半轴（米）
    
    # 计算纬度变化量（弧度转度）
    lat_change = math.degrees(length_meters / EARTH_RADIUS)
    
    # 计算经度变化量（考虑纬度余弦修正）
    lon_change = math.degrees(length_meters / (EARTH_RADIUS * math.cos(math.radians(center_lat))))
    
    north = center_lat + lat_change
    south = center_lat - lat_change
    east = center_lon + lon_change
    west = center_lon - lon_change
    
    # 处理极地特殊情况
    if north > 90:
        north = 90
    if south < -90:
        south = -90
        
        
    polygon_points = []
    for lon in [west, east]:
        for lat in [north, south]:
            polygon_points.append((lon, lat))
    if len(polygon_points) == 4:
        # 如果只有四个点，直接返回外接矩形
        polygon_points = [
            (west, north), (east, north),
            (east, south), (west, south)
        ]
    
    return Polygon(polygon_points).envelope  # 返回外接矩形
def reproject_geometry(geom, source_crs, target_crs):
    """将几何图形从一个坐标系转换到另一个坐标系"""
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return transform(transformer.transform, geom)
def check_geometry_overlap(raster_bbox, geometry):
    """检查几何图形是否与栅格边界框重叠"""
    raster_geom = box(*raster_bbox)
    return raster_geom.intersects(geometry)

def merge_tiles(tiles, zoom, output_path, buffer_polygon):
    """合并多个瓦片为一张大图，并根据缓冲多边形裁剪"""
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    for i, tile in enumerate(tiles):
        tile_url = get_google_tile_url(tile.x, tile.y, zoom)
        img = download_tile(tile_url)
        
        img_array = np.array(img)
        
        if len(img_array.shape) == 2:
            img_array = np.stack([img_array]*3, axis=-1)
        
        temp_file = os.path.join(temp_dir, f"tile_{i}.tif")
        tile_bbox = mercantile.bounds(tile)
        
        transform = from_origin(
            tile_bbox.west,
            tile_bbox.north,
            (tile_bbox.east - tile_bbox.west) / 256,
            (tile_bbox.north - tile_bbox.south) / 256
        )
        
        with rasterio.open(
            temp_file, 'w', driver='GTiff',
            height=img_array.shape[0], width=img_array.shape[1],
            count=3, dtype=img_array.dtype,
            crs=OUTPUT_CRS, transform=transform
        ) as dst:
            for band in range(3):
                dst.write(img_array[:, :, band], band + 1)
        
        temp_files.append(temp_file)
    
    src_files_to_mosaic = []
    for fp in temp_files:
        src = rasterio.open(fp)
        src_files_to_mosaic.append(src)
    
    try:
        mosaic, out_trans = merge(src_files_to_mosaic)
        
        merged_temp_file = os.path.join(temp_dir, "merged_temp.tif")
        
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "crs": "EPSG:4326",
        })
        
        with rasterio.open(merged_temp_file, "w", **out_meta) as dest:
            dest.write(mosaic)
        
        with rasterio.open(merged_temp_file) as src:
            # 获取栅格数据的边界框
            raster_bbox = (
                src.bounds.left, src.bounds.bottom,
                src.bounds.right, src.bounds.top
            )
            
            # 检查多边形与栅格是否重叠
            if not check_geometry_overlap(raster_bbox, buffer_polygon):
                # 计算相交区域
                raster_geom = box(*raster_bbox)
                intersection = raster_geom.intersection(buffer_polygon)
                
                if intersection.is_empty:
                    print("警告: 多边形与栅格数据完全不重叠，返回完整栅格")
                    out_image = mosaic
                    out_transform = out_trans
                else:
                    print("警告: 多边形与栅格数据部分重叠，使用相交区域")
                    geom = [mapping(intersection)]
                    out_image, out_transform = mask.mask(src, geom, crop=True)
            else:
                geom = [json.loads(json.dumps(buffer_polygon.__geo_interface__))]
                out_image, out_transform = mask.mask(src, geom, crop=True)
            
            out_meta = src.meta.copy()
        
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "crs": OUTPUT_CRS
        })
        
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)
        
        array = np.moveaxis(out_image, 0, -1)  # (bands, height, width) -> (height, width, bands)
        image = Image.fromarray(array)
        # 转换为 RGB（防止出现RGBA等格式问题）
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_resized = image.resize((1024, 1024), Image.LANCZOS)
        jpg_subdir = os.path.join(os.path.dirname(output_path), "jpg")
        os.makedirs(jpg_subdir, exist_ok=True)
        jpg_filename = os.path.basename(output_path).replace(".tif", ".jpg")
        jpg_output_path = os.path.join(jpg_subdir, jpg_filename)
        image_resized.save(jpg_output_path, format="JPEG", quality=100)
        print(f"保存 JPG 图像: {jpg_output_path}")
        
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

def process_geojson_points(input_geojson, output_dir):
    """处理GeoJSON文件中的每个点"""
    # 读取GeoJSON文件
    gdf = gpd.read_file(input_geojson)
    
    # 确保数据是WGS84坐标系
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    # 为每个点创建缓冲矩形
    for idx, row in gdf.iterrows():
        point = row.geometry
        if isinstance(point, Point):
            # 转换为Web墨卡托以进行缓冲
            x, y = latlon_to_mercator(point.y, point.x)
            mercator_point = Point(x, y)
            
            # 创建缓冲矩形
            buffer_polygon = mercator_point.buffer(BUFFER_DISTANCE).envelope
            buffer_polygon2 = geodesic_point_buffer(point.x, point.y, BUFFER_DISTANCE2)
            
            # 将缓冲矩形转换回WGS84以获取瓦片
            minx, miny, maxx, maxy = buffer_polygon.bounds
            west, south = mercator_to_latlon(minx, miny)
            east, north = mercator_to_latlon(maxx, maxy)
            
            # 获取边界框内的所有瓦片
            bbox = (west, south, east, north)
            tiles = get_tiles_in_bbox(bbox, ZOOM_LEVEL)

            if tiles:
                # 创建输出文件名
                output_filename = os.path.join(output_dir, f"point_{idx}.tif")
                
                # 下载并合并瓦片
                merge_tiles(tiles, ZOOM_LEVEL, output_filename,buffer_polygon2)
                print(f"Processed point {idx}: {point.x}, {point.y} -> {output_filename}")
            else:
                print(f"No tiles found for point {idx}")

def process_point(lon,lat, output_dir):
    """单点"""

    x, y = latlon_to_mercator(lat, lon)
    mercator_point = Point(x, y)
    
    # 创建缓冲矩形
    buffer_polygon = mercator_point.buffer(BUFFER_DISTANCE).envelope
    buffer_polygon2 = geodesic_point_buffer(lon, lat, BUFFER_DISTANCE2)
    
    # 将缓冲矩形转换回WGS84以获取瓦片
    minx, miny, maxx, maxy = buffer_polygon.bounds
    west, south = mercator_to_latlon(minx, miny)
    east, north = mercator_to_latlon(maxx, maxy)
    
    # 获取边界框内的所有瓦片
    bbox = (west, south, east, north)
    tiles = get_tiles_in_bbox(bbox, ZOOM_LEVEL)

    if tiles:
        # 创建输出文件名
        output_filename = os.path.join(output_dir, f"point_{lon}_{lat}.tif")
        
        # 下载并合并瓦片
        merge_tiles(tiles, ZOOM_LEVEL, output_filename,buffer_polygon2)
        print(f"Processed point : {lon}, {lat} -> {output_filename}")
    else:
        print(f"No tiles found for point {lon}_{lat}")                

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--geojson', type=str, required=False, help='geojson文件路径', default="/work/dev/osw-ai-server/tool/solar_panel.geojson")
    parser.add_argument('--point', type=str, required=True, help='point')
    args = parser.parse_args()
    output_directory = "image" 
    os.makedirs(output_directory, exist_ok=True)
    if args.point:
        # 处理单个点
        lat,lon = map(float, args.point.split(","))
        process_point(lon, lat, output_directory)
    else:
        # 处理GeoJSON文件中的所有点
        input_geojson = args.geojson
        if not os.path.exists(input_geojson):
            raise FileNotFoundError(f"GeoJSON file not found: {input_geojson}")
        process_geojson_points(input_geojson, output_directory)