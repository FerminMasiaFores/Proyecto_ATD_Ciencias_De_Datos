
from almacenamiento.database import (
    crear_tablas,
    guardar_ubicaciones,
    guardar_cartelera
)


# ==========================================
# CAMPOS COMUNES DE UNA PELÍCULA
# ==========================================

CAMPOS_PELICULA = [
    "cadena",
    "id_externo",
    "titulo",
    "titulo_original",
    "generos",
    "duracion",
    "sinopsis",
    "clasificacion",
    "fecha_estreno"
]


# ==========================================
# REGISTRAR UBICACIONES
# ==========================================

def registrar_ubicaciones(cadena, ciudades):

    crear_tablas()

    return guardar_ubicaciones(
        cadena,
        ciudades
    )


# ==========================================
# VALIDAR PELÍCULA NORMALIZADA
# ==========================================

def validar_pelicula(pelicula, cadena):

    if not isinstance(pelicula, dict):
        raise ValueError(
            "Cada película debe ser un diccionario."
        )

    # Comprobar que tiene todos los campos
    for campo in CAMPOS_PELICULA:

        if campo not in pelicula:
            raise ValueError(
                f"Falta el campo obligatorio: {campo}"
            )

    # Comprobar que pertenece a la cadena
    if pelicula["cadena"] != cadena:
        raise ValueError(
            "La cadena de la película no coincide."
        )

    if not pelicula["id_externo"] or not pelicula["titulo"]:
        raise ValueError(
            "La película necesita ID y título."
        )

    if not isinstance(pelicula["generos"], list):
        raise ValueError(
            "Los géneros deben ser una lista."
        )

    return True


# ==========================================
# REGISTRAR CARTELERA
# ==========================================

def registrar_cartelera(
    cadena,
    id_cine,
    nombre_cine,
    peliculas
):

    crear_tablas()

    # Validar antes de modificar SQLite
    for pelicula in peliculas:
        validar_pelicula(pelicula, cadena)

    return guardar_cartelera(
        cadena,
        id_cine,
        nombre_cine,
        peliculas
    )
