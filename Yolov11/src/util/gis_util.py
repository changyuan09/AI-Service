from osgeo import gdal
import geopandas as gpd
from shapely.geometry import (
    Polygon,
    MultiPoint,
    Point,
    MultiPolygon,
)  # at least GEOS 3.11.0  pip install --upgrade shapely
from shapely import concave_hull
from shapely.ops import unary_union, nearest_points
from geopy.distance import geodesic
from scipy.spatial import Delaunay
import numpy as np
import cv2
from sklearn.cluster import DBSCAN


class GisUtil:
    @classmethod
    def merge(cls, coords_list, test):
        # 将坐标列表转换为多边形对象
        # polygons = [Polygon(coords) for coords in coords_list]

        # merged_polygons = []

        # while polygons:
        #     # 从列表中取出第一个多边形
        #     current_polygon = polygons.pop(0)
        #     to_merge = [current_polygon]

        #     # 检查与其他多边形的距离
        #     for other_polygon in polygons[:]:  # 使用切片防止在迭代中修改列表
        #         if current_polygon.distance(other_polygon) < threshold:
        #             to_merge.append(other_polygon)
        #             polygons.remove(other_polygon)

        #     # 合并找到的多边形
        #     merged_polygons.append(unary_union(to_merge))

        return coords_list + test

    @classmethod
    def test(cls, x, y):
        return x + y

    @classmethod
    def _pixelToCoord(
        cls, pixel_x, pixel_y, min_lon, max_lat, pixel_width, pixel_height
    ):
        """基于图片像素坐标转空间坐标

        Args:
            pixel_x (_type_): _description_
            pixel_y (_type_): _description_

        Returns:
            _type_: _description_
        """
        x = min_lon + (pixel_x * pixel_width)
        y = max_lat - (pixel_y * pixel_height)
        return x, y

    @classmethod
    def pixelToLonLatFromTiff(cls, geotransform, feature):
        """基于tiff图片与图片像素坐标转换空间坐标

        Args:
            tiffPath (_type_): _description_
            feature (_type_): _description_

        Returns:
            _type_: _description_
        """
        # dataset = gdal.Open(tiffPath)
        result = []
        # if dataset is None:
        #     return result
        # else:
        #     geotransform = dataset.GetGeoTransform()
        min_lon = geotransform[0]
        max_lat = geotransform[3]
        pixel_width = geotransform[1]
        pixel_height = abs(geotransform[5])
        # 转换并打印经纬度坐标
        for pixel in feature:
            pixel_y = pixel[1]
            pixel_x = pixel[0]
            lat, lon = GisUtil._pixelToCoord(
                pixel_x, pixel_y, min_lon, max_lat, pixel_width, pixel_height
            )
            # result.append([lat, lon])
            result.append(GisUtil.epsg3857ToEpsg4326(lat, lon))
        # dataset = None
        return result

    @classmethod
    def compute_concave_hull(cls, polygon, alpha):
        """
        计算两个多边形的总凹包。

        参数：
            polygon1 (Polygon): 第一个多边形。
            polygon2 (Polygon): 第二个多边形。
            alpha (float): 控制凹包形状的 alpha 参数。

        返回：
            Polygon: 计算得到的总凹包。
        """
        points = MultiPoint(
            # np.array(
            #     list(polygon.exterior.coords) + list(polygon2.exterior.coords),
            #     dtype=np.float32,
            # )
            polygon
        )
        return concave_hull(points, alpha)

    @classmethod
    def epsg3857ToEpsg4326(cls, x3857, y3857):
        gdf = gpd.GeoDataFrame(geometry=[Point(x3857, y3857)], crs="EPSG:3857")
        gdf2 = gdf.to_crs("EPSG:4326")
        return [gdf2.geometry.x[0], gdf2.geometry.y[0]]

    @classmethod
    def epsg4326ToEpsg3857(cls, x4326, y4326):
        gdf = gpd.GeoDataFrame(geometry=[Point(x4326, y4326)], crs="EPSG:4326")
        gdf2 = gdf.to_crs("EPSG:3857")
        return [gdf2.geometry.x[0], gdf2.geometry.y[0]]

    @classmethod
    def mergePolygonsIfClose(cls, coords_list, threshold):
        """
        计算多个多边形之间的距离，并在距离小于阈值时合并它们。

        参数：
            polygons (list of Polygon): 多边形列表。
            threshold (float): 合并的距离阈值。

        返回：
            MultiPolygon: 合并后的多边形。
        """
        # 将坐标列表转换为多边形对象
        polygons = [Polygon(coords) for coords in coords_list]

        merged_polygons = []

        while polygons:
            current_polygon = polygons.pop(0)
            to_merge = [current_polygon]
            for other_polygon in polygons[:]:
                distance = current_polygon.distance(other_polygon)
                print(distance)
                if distance < threshold:
                    to_merge.append(other_polygon)
                    polygons.remove(other_polygon)
            merged_polygon = unary_union(to_merge)
            if isinstance(merged_polygon, MultiPolygon):
                mergeTmp = []
                for poly in merged_polygon.geoms:
                    mergeTmp.extend(list(poly.exterior.coords))
                merged_polygons.append(mergeTmp)
            else:
                merged_polygons.append(list(merged_polygon.exterior.coords))

        return merged_polygons

    @classmethod
    def mergePolygonsIfClose2(cls, coords_list, threshold_m, min_samples=1):
        """
        计算多个多边形之间的最近距离（基于空间距离）），并在距离小于阈值时合并它们。

        参数：
            coords_list (list of list): 多边形坐标的列表，每个多边形坐标是一个点的列表。
            threshold_m (float): 合并的距离阈值（米）。

        返回：
            list of list: 合并后的多边形的坐标列表。
        """

        polygons = [Polygon(coords) for coords in coords_list]
        distance_matrix = cls.calculate_distance_matrix(polygons)

        dbscan = DBSCAN(eps=threshold_m, min_samples=min_samples, metric="precomputed")
        labels = dbscan.fit_predict(distance_matrix)
        merged_polygons = [
            [] for _ in range(len(set(labels)) - (1 if -1 in labels else 0))
        ]

        for i, label in enumerate(labels):
            if label != -1:
                merged_polygons[label].extend(list(polygons[i].exterior.coords))

        return merged_polygons

    @classmethod
    def lonLatToPixel(cls, geotransform, polygon):
        min_lon = geotransform[0]
        max_lat = geotransform[3]
        pixel_width = geotransform[1]
        pixel_height = abs(geotransform[5])

        pixel_coords = []
        for coord in polygon.exterior.coords:
            lon, lat = GisUtil.epsg4326ToEpsg3857(coord[0], coord[1])
            pixel_x = int((lon - min_lon) / pixel_width)
            pixel_y = int((max_lat - lat) / pixel_height)
            pixel_coords.append((pixel_x, pixel_y))

        return pixel_coords

    @classmethod
    # 计算多边形之间的最近边缘距离
    def calculate_distance_matrix(cls, polygons):
        n = len(polygons)
        distance_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    point_a, point_b = nearest_points(polygons[i], polygons[j])
                    distance = geodesic(
                        (point_a.y, point_a.x), (point_b.y, point_b.x)
                    ).meters
                    distance_matrix[i, j] = distance
                else:
                    distance_matrix[i, j] = 0  # 自身距离为0

        return distance_matrix

