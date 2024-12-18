# Ubicación de Servicios
Este repositorio contiene los script SQL, python y archivo config.json para encontrar las mejores ubicaciones para servicios, el ejemplo permite ubicar farmacias en la comuna de Concón, Región de Valparaíso, Chile.

# Los Script
---
Python
---
Primeramente, respecto a liberias el script identifica si estas están o no en el eviroment, de no estar se instalarán automaticamente a la versión en la cual fue desarrollado el script.
- `geopandas`: 0.14.1
- `sqlalchemy`: 2.0.25
- `psycopg2-binary`: 2.9.10

Las capas necesarias para el uso de este script son:
- **Capa de predios** (`type: Polygon`)
- **Capa de Plan Regulador Comunal (PRC)** (`type: Polygon`)
- **Capa de Manzanas censales** (`type: Polygon`)
- **Capa de servicios** (`type: Point`, por ejemplo, farmacias)

El archivo Python contiene "placeholders" que facilitan la interacción con SQL. Para garantizar una integración adecuada, es necesario asignar a cada placeholder el nombre correspondiente de su archivo shapefile. Estos nombres se utilizarán como identificadores de las tablas en SQL, permitiendo que el script genere consultas dinámicas y correctamente adaptadas, en otras palabras, el nombre que se asocie a cada shp será el nombre final de cada tabla. En el caso de shapefiles, se deben ingresar la rutas de los archivos.





```python
shapefiles = {
    "predios": r"ruta_predios",
    "prc": r"ruta_prc",
    "manzanas_censales": r"ruta_manzanas_censales",
    "servicio": r"ruta_farmacias"
}

placeholders = {
    "schema": esquema_entradas,
    "schema_resultados": esquema_resultados,
    "tabla_servicio": "servicio",
    "tabla_manzanas": "prc",
    "tabla_prc": "manzanas_censales",
    "tabla_predios": "predios",
}
```
---
Archivo config.json
---
Contiene los siguientes elementos:
```json
    {
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "passwd": "contraseña",
        "db": "Nombre base de datos",
        "schema_entradas": "datos",
        "schema_resultados": "resultados"}
    }
```
- host corresponde a la conexión con la base de datos (localhost por defecto, pensado en su uso local)
- port: Corresponde al puerto (5432 por defecto, pensado en su uso local)
- user: Corresponde al nombre de usuario en el servidor de Postgres
- paswd: Corresponde a la contraseña del servidor Postgres
- db: Corresponde a la base de datos donde se desarrollaran todos los procesos
- schema_entradas: Corresponde el schema donde se guardaran las tablas georreferenciadas en la db
- schema_resultados: Corresponde a el schema donde se guardará la tabla de resultados en la db.

schema_entradas y schema_resultados son luego usados como nombre para las variables schema y schema_resultados en los placeholders

## Script SQL

### Requisitos de los archivos SHP

Los archivos shapefile deben incluir las siguientes columnas mínimas:

#### Archivo PRC:

- **ZONA**: Corresponde a la zonificación del PRC.
- **UPERM**: Describe la zonificación (puede ser modificada según el contexto).

> **Nota:** El script busca la palabra "comercio" en la columna `UPERM`. Asegúrate de que exista esta columna o actualiza el script.

#### Manzanas censales:

- **TOTAL_PERS**: Representa la población. Este nombre es compatible con los datos del Instituto Nacional de Estadísticas (INE) de Chile. [Enlace a los datos](https://www.ine.gob.cl/herramientas/portal-de-mapas/geodatos-abiertos).


## Resultados

Los predios son filtrados con los siguientes elementos:

- Zonas permitidas para en PRC para localización de servicios
- Manzanas a mas de 500 metros de farmacias
- Se obtiene primera capa de predios

---
Selección de predios
- Se calcula distancia a farmacias por predio y se calcula la población cercana
- se desarrolla puntaje por distancia y población cercana tal que:
  
  $$\text{puntaje} = \text{población} \cdot 0.6 + \text{distancia} \cdot 0.4$$
  
- Se penaliza por cercania a farmacias (entre mas cercano el predio a una farmacia menor puntaje).

Finalmente, se obtiene una capa de predios llamada resultados_predios la cual contiene las siguientes columnas:

- gid
- Geometria
- Puntuacion_final

El usuarió podrá escoger el predio con mayor puntaje o visualizar los diferentes predios con sus diferentes puntajes.
