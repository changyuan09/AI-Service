CREATE TABLE IF NOT EXISTS solar_panel(
    id serial,
    score double precision,
    geom geometry(polygon, 4326),
    create_time timestamp,
    zone_name text,
    zone_id integer,
    city text
);

DELETE FROM waverley_grid
WHERE NOT EXISTS (
        SELECT
            1
        FROM
            waverley
        WHERE
            ST_Intersects(ST_Transform(waverley_grid.geom, 4326), waverley.geom));

-- update 小写 下划线连接
UPDATE
    sydney_part_zone
SET
    lganame = LOWER(REPLACE(lganame, ' ', '_'));

DROP TABLE "CAMPBELLTOWN_grid", "CANADA BAY_grid", "CANTERBURY-BANKSTOWN_grid", "CITY OF PARRAMATTA_grid", "CUMBERLAND_grid", "FAIRFIELD_grid", "GEORGES RIVER_grid", "HUNTERS HILL_grid", "INNER WEST_grid", "KU-RING-GAI_grid", "LANE COVE_grid", "LIVERPOOL_grid", "MOSMAN_grid", "NORTH SYDNEY_grid", "NORTHERN BEACHES_grid", "PENRITH_grid", "RANDWICK_grid", "RYDE_grid", "STRATHFIELD_grid", "SUTHERLAND SHIRE_grid", "SYDNEY_grid", "THE HILLS SHIRE_grid", "WAVERLEY_grid", "WILLOUGHBY_grid", "WOOLLAHRA_grid";

-- CREATE OR REPLACE FUNCTION create_zone_grids()
-- RETURNS void AS $$
-- DECLARE
--     record RECORD;
-- BEGIN
--     FOR record IN SELECT * FROM brisbane_part_zone LOOP
--         EXECUTE format('
--             CREATE TABLE IF NOT EXISTS %I AS
--             SELECT
--                 *
--             FROM
--                 brisbane_part_zone_grid
--             WHERE
--                 ST_Intersects(geom, %L)',
--             'brisbane_'||record.name || '_grid',
--             record.geom);
--     END LOOP;
-- END;
-- $$ LANGUAGE plpgsql;
-- 调用函数
SELECT
    create_zone_grids();

-- create city grid by au_all_city data
CREATE OR REPLACE FUNCTION create_city_grid(city_name text, grid_size float DEFAULT 100, target_srid integer DEFAULT 3857)
    RETURNS text
    AS $$
DECLARE
    table_name text;
    result_msg text;
    grid_count integer;
    deleted_count integer;
BEGIN
    -- 创建表名（替换空格为下划线）
    table_name := LOWER(REPLACE(TRIM(city_name), ' ', '_')) || '_grid';
    -- 检查表是否存在，若存在则删除
    EXECUTE format('DROP TABLE IF EXISTS %I', table_name);
    -- 创建网格表
    EXECUTE format('
        CREATE TABLE %I (
            id SERIAL PRIMARY KEY,
            geom GEOMETRY(POLYGON, %s),
            is_deal BOOLEAN DEFAULT FALSE
        )', table_name, target_srid);
    -- 插入网格数据
    EXECUTE format('
        INSERT INTO %I (geom, is_deal)
        SELECT 
            (g).geom,
            FALSE
        FROM (
            SELECT ST_SquareGrid(%s, ST_Transform(geom, %s)) AS g
            FROM au_all_city
            WHERE name = %L
        ) AS grids', table_name, grid_size, target_srid, city_name);
    -- 获取插入的网格数量
    EXECUTE format('SELECT COUNT(*) FROM %I', table_name) INTO grid_count;
    -- 删除不与城市边界相交的网格
    EXECUTE format('
        DELETE FROM %I
        WHERE NOT EXISTS (
            SELECT 1
            FROM au_all_city
            WHERE name = %L
            AND ST_Intersects(ST_Transform(%I.geom, 4326), au_all_city.geom)
        )', table_name, city_name, table_name);
    -- 获取删除的网格数量
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    -- 创建空间索引
    EXECUTE format('CREATE INDEX %I_geom_idx ON %I USING GIST(geom)', table_name, table_name);
    -- 返回执行结果
    result_msg := format('
        已为城市 "%s" 创建网格表 %s:
        - 生成网格总数: %s
        - 删除无效网格: %s
        - 最终网格数量: %s', city_name, table_name, grid_count, deleted_count, grid_count - deleted_count);
    RETURN result_msg;
EXCEPTION
    WHEN OTHERS THEN
        RETURN '错误: ' || SQLERRM;
END;

$$
LANGUAGE plpgsql;

SELECT
    create_city_grid('brisbane');

SELECT
    create_city_grid('ballarat');

SELECT
    create_city_grid('perth');

SELECT
    create_city_grid('townsville');

SELECT
    create_city_grid('adelaide');

SELECT
    create_city_grid('canberra');

SELECT
    create_city_grid('newcastle');

SELECT
    create_city_grid('gosford');

SELECT
    create_city_grid('bendigo');

SELECT
    create_city_grid('wollongong');

SELECT
    create_city_grid('geelong');

SELECT
    create_city_grid('wodonga');

SELECT
    create_city_grid('albury');

SELECT
    create_city_grid('hobart');

SELECT
    create_city_grid('cairns');

SELECT
    create_city_grid('toowoomba');

SELECT
    create_city_grid('darwin');

