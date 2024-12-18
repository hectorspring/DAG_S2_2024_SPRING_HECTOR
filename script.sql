-- 1. Cambiar proyección de todas las capas
ALTER TABLE "{schema}"."{tabla_farmacias}"
ALTER COLUMN geometry TYPE geometry(Point, 3857)
USING ST_Transform(geometry, 3857);

ALTER TABLE "{schema}"."{tabla_manzanas}"
ALTER COLUMN geometry TYPE geometry(MultiPolygon, 3857)
USING ST_Transform(geometry, 3857);

ALTER TABLE "{schema}"."{tabla_prc}"
ALTER COLUMN geometry TYPE geometry(MultiPolygon, 3857)
USING ST_Transform(geometry, 3857);

ALTER TABLE "{schema}"."{tabla_predios}"
ALTER COLUMN geometry TYPE geometry(MultiPolygon, 3857)
USING ST_Transform(geometry, 3857);

-- 2. Crear tabla temporal con zonas permitidas (zonas con comercio)
DROP TABLE IF EXISTS zonas_permitidas;
CREATE TEMP TABLE zonas_permitidas AS
SELECT DISTINCT "ZONA"
FROM "{schema}"."{tabla_prc}"
WHERE "UPERM" ILIKE '%comercio%';

-- 3. Filtrar zonas permitidas
DROP TABLE IF EXISTS prc_filtradas;
CREATE TEMP TABLE prc_filtradas AS
SELECT *
FROM "{schema}"."{tabla_prc}"
WHERE "ZONA" IN (SELECT "ZONA" FROM zonas_permitidas);

-- 4. Excluir zonas con farmacias dentro de 500 metros
DROP TABLE IF EXISTS zonas_sin_farmacias;
CREATE TEMP TABLE zonas_sin_farmacias AS
SELECT zonas.*
FROM prc_filtradas AS zonas
WHERE NOT EXISTS (
    SELECT 1
    FROM "{schema}"."{tabla_farmacias}" AS farmacias
    WHERE ST_Intersects(zonas.geometry, ST_Buffer(farmacias.geometry, 500))
);

-- 5. Seleccionar predios que intersectan con zonas sin farmacias
DROP TABLE IF EXISTS predios_filtrados;
CREATE TEMP TABLE predios_filtrados AS
SELECT predios.*
FROM "{schema}"."{tabla_predios}" AS predios
JOIN zonas_sin_farmacias AS zonas
ON ST_Intersects(predios.geometry, zonas.geometry);

-- 6. Excluir predios cercanos a farmacias dentro de 200 metros
DROP TABLE IF EXISTS predios_elegibles;
CREATE TEMP TABLE predios_elegibles AS
SELECT *
FROM predios_filtrados
WHERE gid NOT IN (
    SELECT predios.gid
    FROM predios_filtrados AS predios
    JOIN "{schema}"."{tabla_farmacias}" AS farmacias
    ON ST_DWithin(predios.geometry, farmacias.geometry, 200)
);

-- 7. Asociar predios con manzanas y calcular población
DROP TABLE IF EXISTS predios_manzanas;
CREATE TEMP TABLE predios_manzanas AS
SELECT 
    predios.gid AS predio_id,
    manzanas.gid AS manzana_id,
    manzanas."TOTAL_PERS" AS poblacion,
    predios.geometry AS geom_predio
FROM predios_elegibles AS predios
JOIN "{schema}"."{tabla_manzanas}" AS manzanas
ON ST_Intersects(predios.geometry, manzanas.geometry);

-- 8. Calcular distancia mínima a farmacias y población cercana
DROP TABLE IF EXISTS "{schema_resultados}"."resultado_predios";
CREATE TABLE "{schema_resultados}"."resultado_predios" AS  
WITH distancia AS (
    SELECT 
        p.predio_id AS gid, 
        COALESCE(MIN(ST_Distance(p.geom_predio, f.geometry)), 5000) AS dist
    FROM predios_manzanas p
    LEFT JOIN "{schema}"."{tabla_farmacias}" f 
    ON ST_DWithin(p.geom_predio, f.geometry, 5000)
    GROUP BY p.predio_id
),
poblacion AS (
    SELECT 
        p.predio_id AS gid, 
        SUM(m."TOTAL_PERS") AS pop
    FROM predios_manzanas p
    JOIN "{schema}"."{tabla_manzanas}" m 
    ON ST_Intersects(ST_Buffer(p.geom_predio, 500), m.geometry)
    GROUP BY p.predio_id
),
puntuacion AS (
    SELECT 
        d.gid, 
        (d.dist * 0.4) + (p.pop * 0.6) AS puntuacion_final
    FROM distancia d
    LEFT JOIN poblacion p 
    ON d.gid = p.gid
)
SELECT 
    p.predio_id AS gid, 
    p.geom_predio AS geometry, 
    COALESCE(pt.puntuacion_final, 0) AS puntuacion_final
FROM predios_manzanas p
LEFT JOIN puntuacion pt 
ON p.predio_id = pt.gid;
