# Ubicación de Servicios
Este repositorio contiene los script SQL, python y archivo config.json para encontrar las mejores ubicaciones para servicios, el ejemplo permite ubicar farmacias en la comuna de Concón, Región de Valparaíso, Chile.

# Los Script
---
Python
---
Primeramente, respecto a liberias el script identifica si estas están o no en el eviroment, de no estar se instalarán automaticamente a la versión en la cual fue desarrollado el script.
- geopandas": "0.14.1
- sqlalchemy": "2.0.25
- psycopg2-binary: "2.9.10"
Las capas necesarias para el uso de este script son:
- Capa de predios (type: Polygon), Capa de Plan Regulador Comunal (PRC) (type: Polygon), capa Manzanas censales (type: Polygon) y capa de servicio (type: point). En mi caso, farmacias.

El archivo Python contiene "placeholders" que facilitan la interacción con SQL. Para garantizar una integración adecuada, es necesario asignar a cada placeholder el nombre correspondiente de su archivo shapefile. Estos nombres se utilizarán como identificadores de las tablas en SQL, permitiendo que el script genere consultas dinámicas y correctamente adaptadas, en otras palabras, el nombre que se asocie a cada shp será el nombre final de cada tabla. En el caso de shapefiles, se deben ingresar la rutas de los archivos.






      shapefiles = {
        "predios": r"ruta_predios",
        "prc": r"ruta_prc",
        "manzanas_censales": r"ruta_manzanas_censales",
        "farmacias": r"ruta_farmacias"
      }
      placeholders = {
        "schema": esquema_entradas,
        "schema_resultados": esquema_resultados,
        "tabla_farmacias": "farmacias",
        "tabla_manzanas": "prc",
        "tabla_prc": "manzanas_censales",
        "tabla_predios": "predios",
      }
  
---
Archivo config.json
---
Contiene los siguientes elementos:

    {
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "passwd": "pgadmin",
        "db": "PEP_DAG2",
        "schema_entradas": "datos",
        "schema_resultados": "resultados"}
    }
- host corresponde a la conexión con la base de datos (localhost por defecto, pensado en su uso local)
- port: Corresponde al puerto
- user: Corresponde al nombre de usuario en el servidor de Postgres
- paswd: Corresponde a la contraseña del servidor Postgres
- db: Corresponde a la base de datos donde se desarrollaran todos los procesos
- schema_entradas: Corresponde el schema donde se guardaran las tablas georreferenciadas en la db
- schema_resultados: Corresponde a el schema donde se guardará la tabla de resultados en la db.

schema_entradas y schema_resultados son luego usados como nombre para las variables schema y schema_resultados en los placeholders

---
Script SQL
---

Lo importante en este caso es conocer los archivos SHP y sus columnas los archivos deben tener al menos las siguientes columnas

- Archivo PRC: Debe contener la columna ZONA que corresponde a la zonificación propia de un PRC y la columna UPERM que en muchos casos es un descripción de zonificación, de lo contrario se debe cambiar esta columna en el script para que concuerde con la info minima. El script busca la coincidencia de "comercio" en la columna UPERM, es imperativo que el usuario asegure que existe esta columna.
- Manzanas censales: Respecto a las manzanas estas deben contener una columna que contenga población, en el script se llama a la columna por el nombre "TOTAL_PERS", dado que se desarrolló con la capa de manzanas entregada por el Instituto Nacional de Estadistica (INE) de Chile, por lo que se recomienda su uso: https://www.ine.gob.cl/herramientas/portal-de-mapas/geodatos-abiertos.
