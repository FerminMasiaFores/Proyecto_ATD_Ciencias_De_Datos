
import json
import sqlite3
from pathlib import Path


# ==========================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ==========================================

RUTA_BD = (
    Path(__file__).resolve().parent.parent
    / "datos"
    / "cinedata.db"
)


def conectar():
    RUTA_BD.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conexion = sqlite3.connect(RUTA_BD)

    conexion.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conexion


# ==========================================
# CREAR LAS TABLAS
# ==========================================

def crear_tablas():

    conexion = conectar()

    try:
        with conexion:

            conexion.executescript("""
                CREATE TABLE IF NOT EXISTS cines (
                    cadena TEXT NOT NULL,
                    id_externo TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    PRIMARY KEY (cadena, id_externo)
                );

                CREATE TABLE IF NOT EXISTS peliculas (
                    cadena TEXT NOT NULL,
                    id_externo TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    titulo_original TEXT,
                    generos TEXT,
                    duracion TEXT,
                    sinopsis TEXT,
                    clasificacion TEXT,
                    fecha_estreno TEXT,
                    PRIMARY KEY (cadena, id_externo)
                );

                CREATE TABLE IF NOT EXISTS cine_pelicula (
                    cadena TEXT NOT NULL,
                    id_cine TEXT NOT NULL,
                    id_pelicula TEXT NOT NULL,

                    PRIMARY KEY (
                        cadena,
                        id_cine,
                        id_pelicula
                    ),

                    FOREIGN KEY (cadena, id_cine)
                        REFERENCES cines (
                            cadena,
                            id_externo
                        ),

                    FOREIGN KEY (cadena, id_pelicula)
                        REFERENCES peliculas (
                            cadena,
                            id_externo
                        )
                );
                
                CREATE TABLE IF NOT EXISTS ciudades (
                    cadena TEXT NOT NULL,
                    id_externo TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                
                    PRIMARY KEY (cadena, id_externo)
                );
                
                CREATE TABLE IF NOT EXISTS cine_ciudad (
                    cadena TEXT NOT NULL,
                    id_cine TEXT NOT NULL,
                    id_ciudad TEXT NOT NULL,
                
                    PRIMARY KEY (cadena, id_cine),
                
                    FOREIGN KEY (cadena, id_cine)
                        REFERENCES cines (cadena, id_externo),
                
                    FOREIGN KEY (cadena, id_ciudad)
                        REFERENCES ciudades (cadena, id_externo)
                );

            """)

    finally:
        conexion.close()


# ==========================================
# GUARDAR PELÍCULAS DE UN CINE
# ==========================================

def guardar_cartelera(
    cadena,
    id_cine,
    nombre_cine,
    peliculas
):

    if not peliculas:
        raise ValueError(
            "No se puede guardar una lista vacía."
        )

    conexion = conectar()

    try:
        with conexion:

            # Guardar o actualizar el cine
            conexion.execute("""
                INSERT INTO cines (
                    cadena,
                    id_externo,
                    nombre
                )
                VALUES (?, ?, ?)

                ON CONFLICT(cadena, id_externo)
                DO UPDATE SET
                    nombre = excluded.nombre
            """, (
                cadena,
                id_cine,
                nombre_cine
            ))

            # Actualizar las relaciones de este cine
            conexion.execute("""
                DELETE FROM cine_pelicula
                WHERE cadena = ?
                AND id_cine = ?
            """, (cadena, id_cine))

            for pelicula in peliculas:

                if pelicula["cadena"] != cadena:
                    raise ValueError(
                        "La cadena de la película "
                        "no coincide con el cine."
                    )

                # Guardar o actualizar película
                conexion.execute("""
                    INSERT INTO peliculas (
                        cadena,
                        id_externo,
                        titulo,
                        titulo_original,
                        generos,
                        duracion,
                        sinopsis,
                        clasificacion,
                        fecha_estreno
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

                    ON CONFLICT(cadena, id_externo)
                    DO UPDATE SET
                        titulo = excluded.titulo,
                        titulo_original = excluded.titulo_original,
                        generos = excluded.generos,
                        duracion = excluded.duracion,
                        sinopsis = excluded.sinopsis,
                        clasificacion = excluded.clasificacion,
                        fecha_estreno = excluded.fecha_estreno
                """, (
                    pelicula["cadena"],
                    pelicula["id_externo"],
                    pelicula["titulo"],
                    pelicula["titulo_original"],
                    json.dumps(
                        pelicula["generos"],
                        ensure_ascii=False
                    ),
                    pelicula["duracion"],
                    pelicula["sinopsis"],
                    pelicula["clasificacion"],
                    pelicula["fecha_estreno"]
                ))

                # Relacionar película con cine
                conexion.execute("""
                    INSERT INTO cine_pelicula (
                        cadena,
                        id_cine,
                        id_pelicula
                    )
                    VALUES (?, ?, ?)
                """, (
                    cadena,
                    id_cine,
                    pelicula["id_externo"]
                ))

    finally:
        conexion.close()

    return len(peliculas)


# ==========================================
# CONSULTAR PELÍCULAS GUARDADAS
# ==========================================

def consultar_peliculas_de_cine(
    cadena,
    id_cine
):

    conexion = conectar()

    try:
        cursor = conexion.execute("""
            SELECT p.titulo
            FROM peliculas p

            JOIN cine_pelicula cp
            ON p.cadena = cp.cadena
            AND p.id_externo = cp.id_pelicula

            WHERE cp.cadena = ?
            AND cp.id_cine = ?

            ORDER BY p.titulo COLLATE NOCASE
        """, (cadena, id_cine))

        return [
            fila[0]
            for fila in cursor.fetchall()
        ]

    finally:
        conexion.close()


# ==========================================
# GUARDAR CIUDADES Y CINES DE YELMO
# ==========================================


# ==========================================
# GUARDAR UBICACIONES DE CUALQUIER CADENA
# ==========================================

def guardar_ubicaciones(cadena, ciudades):

    if not isinstance(cadena, str) or not cadena.strip():
        raise ValueError("La cadena no puede estar vacía.")

    cadena = cadena.strip()

    conexion = conectar()

    total_ciudades = 0
    total_cines = 0

    try:
        with conexion:

            for ciudad in ciudades:

                id_ciudad = ciudad["id"]
                nombre_ciudad = ciudad["nombre"]

                # Guardar o actualizar ciudad
                conexion.execute("""
                    INSERT INTO ciudades (
                        cadena,
                        id_externo,
                        nombre
                    )
                    VALUES (?, ?, ?)

                    ON CONFLICT(cadena, id_externo)
                    DO UPDATE SET
                        nombre = excluded.nombre
                """, (
                    cadena,
                    id_ciudad,
                    nombre_ciudad
                ))

                total_ciudades += 1

                # Guardar los cines de la ciudad
                for cine in ciudad["cines"]:

                    id_cine = cine["id"]
                    nombre_cine = cine["nombre"]

                    conexion.execute("""
                        INSERT INTO cines (
                            cadena,
                            id_externo,
                            nombre
                        )
                        VALUES (?, ?, ?)

                        ON CONFLICT(cadena, id_externo)
                        DO UPDATE SET
                            nombre = excluded.nombre
                    """, (
                        cadena,
                        id_cine,
                        nombre_cine
                    ))

                    # Relacionar cine con ciudad
                    conexion.execute("""
                        INSERT INTO cine_ciudad (
                            cadena,
                            id_cine,
                            id_ciudad
                        )
                        VALUES (?, ?, ?)

                        ON CONFLICT(cadena, id_cine)
                        DO UPDATE SET
                            id_ciudad = excluded.id_ciudad
                    """, (
                        cadena,
                        id_cine,
                        id_ciudad
                    ))

                    total_cines += 1

    finally:
        conexion.close()

    return total_ciudades, total_cines


# ==========================================
# COMPATIBILIDAD CON EL CÓDIGO DE YELMO
# ==========================================

def guardar_ubicaciones_yelmo(ciudades):

    return guardar_ubicaciones(
        "Yelmo",
        ciudades
    )
