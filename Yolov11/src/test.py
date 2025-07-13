import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
from algorithm import boundary_regularization_from_polygon
import numpy as np
import cv2


def smooth_polygon(polygon, tolerance=0.01):
    """平滑多边形"""
    return polygon.simplify(tolerance, preserve_topology=True)


def testMaskToVector():
    """google的Mask转换矢量"""
    raster_path = "/home/jovyan/dev/osw-ai-server/data/mask_java_test2.tiff"
    with rasterio.open(raster_path) as src:
        image = src.read(1)
        mask = image != 0

        results = shapes(image, mask=mask, transform=src.transform)

    geometries = []
    values = []
    for geom, value in results:
        shapely_geom = shape(geom)
        points = np.array(shapely_geom.exterior.coords)
        polygonReg = boundary_regularization_from_polygon(
            points, epsilon=0.3
        )  # pixel size 0.1-0.2
        # polygonReg = boundary_regularization_from_polygon(
        #     points, epsilon=1
        # )  # pixel size 0.5

        if (
            polygonReg.shape[0] > 0 and len(polygonReg) >= 4
        ):  # Ensure there are points to create a geometry
            polygonReg_geom = shape({"type": "Polygon", "coordinates": [polygonReg]})
            smoothed_geom = smooth_polygon(polygonReg_geom, tolerance=1)
            geometries.append(smoothed_geom)
            # polygonReg_geom = shape(
            #     {"type": "Polygon", "coordinates": [polygonReg.tolist()]}
            # )
            # geometries.append(polygonReg_geom)
            values.append(value)
    gdf = gpd.GeoDataFrame({"geometry": geometries, "value": values}, crs=src.crs)

    # Export to GeoJSON
    gdf.to_file("data/res/mask_java_test2-1.geojson", driver="GeoJSON")


def testImagePresion(imgPath):
    """厕所nearmap和google的图片分辨率"""
    image = cv2.imread(imgPath)
    img2gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    imageVar = cv2.Laplacian(img2gray, cv2.CV_64F).var()

    return imageVar


if __name__ == "__main__":
    testMaskToVector()
    # print(
    #     testImagePresion(
    #         "/home/jovyan/dev/osw-ai-server/data/google_replace_nearmap/google_img3_on.tif"
    #     )
    # )
