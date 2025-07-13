import psycopg2
from psycopg2.extras import DictCursor
import numpy as np
from psycopg2 import pool

conn_params = {"host": "110.185.170.154", "database": "gis", "user": "postgres", "password": "postgis", "port": "5432"}
# conn_params = {
#     "host": "host.docker.internal",
#     "database": "gis",
#     "user": "postgres",
#     "password": "postgres",
#     "port": "5432",
# }

connection_pool = psycopg2.pool.SimpleConnectionPool(minconn=1, maxconn=50, **conn_params)


def check_table(solar_panel_table):
    cursor = None
    conn = None
    try:
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {solar_panel_table} (
            id serial PRIMARY KEY,
            score double precision,
            geom geometry(polygon, 4326),
            create_time timestamp,
            zone_name varchar,
            zone_id integer,
            city varchar
        );
        """

        cursor.execute(create_table_query)
        conn.commit()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            connection_pool.putconn(conn)


def get_city_info(city_name):
    if city_name is None:
        cursor = None
        conn = None
        try:
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(f"SELECT  name FROM au_all_city order by name")
            citys = cursor.fetchall()
            return citys
        except Exception as e:
            print(f"Error fetching data : {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        return city_name


def get_grids(grid_table_name):
    cursor = None
    conn = None
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=DictCursor)

        cursor.execute(f"SELECT geom,id,is_deal FROM {grid_table_name}")
        polygons = cursor.fetchall()

        return polygons

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_grid_status(grid_id, is_deal, grid_table_name):
    cursor = None
    conn = None
    try:
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {grid_table_name} SET is_deal = {is_deal} WHERE id = {grid_id}")
        conn.commit()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            connection_pool.putconn(conn)


def insert_solar_panel(solar_panel_table, scores, geoms, zone_name, city_name, zone_id):
    is_success = True
    cursor = None
    conn = None
    try:
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        for score, geom in zip(scores, geoms):
            score_float = float(score) if hasattr(score, "item") else score
            geom_box_wkt = f"POLYGON(({geom[0][1]} {geom[0][0]},{geom[1][1]} {geom[0][0]},{geom[1][1]} {geom[1][0]},{geom[0][1]} {geom[1][0]},{geom[0][1]} {geom[0][0]}))"
            cursor.execute(
                f"INSERT INTO {solar_panel_table} (score, geom, create_time, zone_name,zone_id,city) VALUES (%s,ST_GeomFromText( %s), NOW(), %s, %s, %s)",
                (score_float, geom_box_wkt, zone_name, zone_id, city_name),
            )
        conn.commit()

    except Exception as e:
        print(f"Error: {e}")
        is_success = False
    finally:
        if cursor:
            cursor.close()
        if conn:
            connection_pool.putconn(conn)
    return is_success
