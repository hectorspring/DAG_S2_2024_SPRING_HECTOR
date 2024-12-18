import json
import geopandas as gpd
from sqlalchemy import create_engine, text
from geoalchemy2 import Geometry
from sqlalchemy.exc import SQLAlchemyError
import sys
import subprocess
import logging

logging.basicConfig()

logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
def verificar_e_instalar_dependencias():
# Verifica si las dependencias necesarias están instaladas. 
    dependencias = {
        "geopandas": "0.14.1",
        "sqlalchemy": "2.0.25",
        "psycopg2": "2.9.10"
    }

    for paquete, version in dependencias.items():
        try:
            # Intentar importar la dependencia
            __import__(paquete)
        except ImportError:
            print(f"No se encontró el paquete '{paquete}'. Instalando versión {version}...")
            try:
                # Instalar el paquete con pip
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", f"{paquete}=={version}"]
                )
                print(f"'{paquete}' instalado correctamente.")
            except subprocess.CalledProcessError:
                print(f"Error al instalar '{paquete}'. Verifica la conexión a Internet o permisos.")
                sys.exit(1)

# Llama a la función al inicio del programa
verificar_e_instalar_dependencias()

# Leer archivo de configuración
def cargar_config(ruta_config):
    with open(ruta_config, 'r') as file:
        return json.load(file)

# Habilitar extensión PostGIS
def habilitar_postgis(engine):
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
        print("Extensión PostGIS habilitada correctamente.")
    except SQLAlchemyError as e:
        print(f"Error al habilitar PostGIS: {e}")

# Crear esquemas en la base de datos
def crear_esquema_si_no_existe(engine, esquema):
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {esquema};"))
            conn.commit()
        print(f"Esquema '{esquema}' creado o ya existía.")
    except SQLAlchemyError as e:
        print(f"Error creando el esquema '{esquema}': {e}")

# Cargar shapefile a PostgreSQL
def cargar_shapefile_a_postgis(ruta_shp, engine, esquema, nombre_tabla, srid=3857):
    # Crear el esquema si no existe
    crear_esquema_si_no_existe(engine, esquema)
    
    # Leer el shapefile con GeoPandas
    gdf = gpd.read_file(ruta_shp)
    
    # Asegurarse de que el CRS está configurado
    if gdf.crs is None:
        print(f"El shapefile {ruta_shp} no tiene CRS. Asignando WGS 84 (EPSG:{srid}).")
        gdf.set_crs(epsg=srid, inplace=True)
    
    # Cargar los datos en PostgreSQL
    try:
        gdf.to_postgis(
            nombre_tabla,
            engine,
            schema=esquema,
            if_exists="replace",
            index=True,
            index_label="gid",
            dtype={"geometry": Geometry("MULTIPOLYGON", srid=srid)}
        )
        print(f"Tabla '{esquema}.{nombre_tabla}' creada exitosamente.")
    except SQLAlchemyError as e:
        print(f"Error cargando el shapefile '{ruta_shp}' en la tabla '{esquema}.{nombre_tabla}': {e}")

def procesar_placeholders(ruta_sql, placeholders):
    """
    Lee un archivo SQL y reemplaza placeholders dinámicamente.
    """
    try:
        with open(ruta_sql, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        # Reemplazar placeholders en el script SQL
        return sql_script.format(**placeholders)
    except Exception as e:
        raise RuntimeError(f"Error al procesar placeholders en el script SQL: {e}")

# Modificar ejecutar_script_sql para aceptar el SQL procesado
def ejecutar_script_sql(engine, sql_script):
    """
    Ejecuta un script SQL procesado con placeholders en PostgreSQL.
    """
    try:
        with engine.begin() as conn:  # Usa "begin" para manejar transacciones automáticamente
            for statement in sql_script.split(";"):
                if statement.strip():  # Evitar ejecutar líneas vacías
                    conn.execute(text(statement))
        print("Script SQL ejecutado correctamente.")
    except Exception as e:
        print(f"Error al ejecutar el script SQL: {e}")

# Código principal
if __name__ == "__main__":
    ruta_config = "config.json"
    ruta_sql = "script.sql"

    # Cargar configuración
    config = cargar_config(ruta_config)
    db_config = config["database"]

    # Crear conexión con la base de datos
    engine = create_engine(
        f"postgresql+psycopg2://{db_config['user']}:{db_config['passwd']}@{db_config['host']}:{db_config['port']}/{db_config['db']}")
    
    engine.connect()


    # Habilitar PostGIS
    habilitar_postgis(engine)

    # Crear esquemas
    esquema_entradas = db_config["schema_entradas"]
    esquema_resultados = db_config["schema_resultados"]

    crear_esquema_si_no_existe(engine, esquema_entradas)
    crear_esquema_si_no_existe(engine, esquema_resultados)



    # Cargar shapefiles
    shapefiles = {
        "predios": r"rutas_predios",
        "prc": r"rutas_prc",
        "manzanas_censales": r"ruta_manzanas",
        "servicios": r"ruta_servicios"
    }

    for nombre_tabla, ruta_shp in shapefiles.items():
        cargar_shapefile_a_postgis(ruta_shp, engine, esquema_entradas, nombre_tabla)

    # Placeholder para el script SQL
    placeholders = {
        "schema": esquema_entradas,
        "schema_resultados": esquema_resultados,
        "tabla_farmacias": "servicios",
        "tabla_manzanas": "manzanas_censales",
        "tabla_prc": "prc",
        "tabla_predios": "predios",
    }

    # Leer y procesar el script SQL con placeholders
    sql_script = procesar_placeholders(ruta_sql, placeholders)

    # Ejecutar el script SQL procesado
    ejecutar_script_sql(engine, sql_script)

    engine.dispose()
    print("Conexión a la base de datos cerrada.")