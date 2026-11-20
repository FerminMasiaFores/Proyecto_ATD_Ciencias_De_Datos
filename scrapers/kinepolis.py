import json
from datetime import datetime
from pathlib import Path

import requests


# ==========================================
# CONFIGURACIÓN
# ==========================================

# Petición de la web de Kinépolis que devuelve sesiones y películas.
# Se copia desde la pestaña "Red" del navegador. Si se deja vacía
# o la descarga falla, se usa el JSON guardado en la carpeta datos.
URL_CARTELERA = ""

ARCHIVO_LOCAL = (
    Path(__file__).resolve().parent.parent
    / "datos" / "kinepolis_cartelera.json"
)

# Aquí se guarda la cartelera para no leerla cada vez
_cartelera = None


# ==========================================
# CARGAR LA CARTELERA
# ==========================================

def _descargar_cartelera():

    respuesta = requests.get(URL_CARTELERA, timeout=20)

    print("Código HTTP (Kinépolis):", respuesta.status_code)

    respuesta.raise_for_status()

    return respuesta.json()


def _leer_archivo_local():

    print("Usando el archivo local:", ARCHIVO_LOCAL.name)

    with open(ARCHIVO_LOCAL, encoding="utf-8") as f:
        return json.load(f)


def cargar_cartelera():

    global _cartelera

    if _cartelera is not None:
        return _cartelera

    datos = None

    # 1) Intentar descargarla de la web
    if URL_CARTELERA:
        try:
            datos = _descargar_cartelera()

        except (requests.RequestException, ValueError) as error:
            print("No se ha podido descargar la cartelera:", error)

    # 2) Si no se puede, leer el JSON guardado desde el navegador
    if datos is None:
        datos = _leer_archivo_local()

    _cartelera = {
        "sesiones": datos.get("sessions") or [],
        "peliculas": datos.get("films") or []
    }

    return _cartelera
# ==========================================
# LIMPIEZA DE DATOS
# ==========================================

# Idiomas que aparecen en "rawSessionAttributes"
IDIOMAS = {
    "Spanish": "Español",
    "English": "Inglés",
    "Catalan": "Catalán",
    "French": "Francés",
    "Italian": "Italiano",
    "Japanese": "Japonés",
    "Korean": "Coreano",
    "Hindi": "Hindi"
}

# Subtítulos que aparecen en "rawSessionAttributes"
SUBTITULOS = {
    "es": "español",
    "en": "inglés"
}


def _hora_sesion(sesion):

    # La hora viene como "2026-11-13T16:00:00+00:00".
    # Nos quedamos con la fecha y la hora tal cual.
    return datetime.fromisoformat(sesion["showtime"][:19])


def _sesiones_futuras(cine):

    ahora = datetime.now()

    return [
        sesion
        for sesion in cargar_cartelera()["sesiones"]
        if sesion.get("complexOperator") == cine
        and _hora_sesion(sesion) >= ahora
    ]


def _version(atributos):

    # Ejemplo de atributos: "2D,English,es"
    etiquetas = atributos.split(",")

    idioma = next(
        (IDIOMAS[e] for e in etiquetas if e in IDIOMAS),
        "Idioma no disponible"
    )

    subtitulos = next(
        (SUBTITULOS[e] for e in etiquetas if e in SUBTITULOS),
        None
    )

    if idioma == "Español" and subtitulos is None:
        return "Castellano"

    if subtitulos:
        return f"{idioma} (subtítulos en {subtitulos})"

    return idioma


def _limpiar_pelicula(pelicula):

    estreno = (pelicula.get("releaseDate") or "")[:10]

    sinopsis = (
        (pelicula.get("synopsis") or "")
        .replace("\r\n", "\n")
        .strip()
    )

    return {
        "id": pelicula.get("id"),
        "titulo": pelicula.get("title") or "Sin título",
        "duracion": pelicula.get("duration"),
        "edad": (pelicula.get("censor") or {}).get("name"),
        "generos": [
            genero["name"]
            for genero in pelicula.get("genres") or []
            if genero.get("name")
        ],
        "idioma": (pelicula.get("spokenLanguage") or {}).get("name"),
        "estreno": estreno,
        "distribuidora": pelicula.get("distributorName"),
        "sinopsis": sinopsis
    }


# ==========================================
# OBTENER TODOS LOS CINES KINÉPOLIS
# ==========================================

def obtener_cines():

    cines = {}

    for sesion in cargar_cartelera()["sesiones"]:

        identificador = sesion.get("complexOperator")
        nombre = sesion.get("cinemaLabel")

        if identificador and nombre:
            cines[identificador] = nombre

    lista = [
        {"id": identificador, "nombre": nombre}
        for identificador, nombre in cines.items()
    ]

    # Ordenar los cines alfabéticamente
    return sorted(lista, key=lambda c: c["nombre"].casefold())


# ==========================================
# OBTENER PELÍCULAS DE UN CINE
# ==========================================

def obtener_peliculas(cine):

    # Guardar en qué formatos se proyecta cada película
    # (el formato viene en cada sesión, no en la película)
    formatos_por_pelicula = {}

    for sesion in _sesiones_futuras(cine):

        identificador = sesion["film"]["id"]
        formato = (sesion["film"].get("format") or {}).get("name")

        if identificador not in formatos_por_pelicula:
            formatos_por_pelicula[identificador] = set()

        if formato:
            formatos_por_pelicula[identificador].add(formato)

    peliculas = []

    for pelicula in cargar_cartelera()["peliculas"]:

        if pelicula.get("id") in formatos_por_pelicula:

            datos = _limpiar_pelicula(pelicula)
            datos["formatos"] = sorted(formatos_por_pelicula[pelicula["id"]])
            peliculas.append(datos)

    return sorted(peliculas, key=lambda p: p["titulo"].casefold())


# ==========================================
# OBTENER SESIONES DE UNA PELÍCULA
# ==========================================

def obtener_sesiones(cine, id_pelicula):

    sesiones = []

    for sesion in _sesiones_futuras(cine):

        if sesion["film"]["id"] != id_pelicula:
            continue

        sesiones.append({
            "fecha": _hora_sesion(sesion),
            "sala": sesion.get("hall"),
            "formato": (
                (sesion["film"].get("format") or {}).get("name")
                or "No disponible"
            ),
            "version": _version(
                sesion.get("rawSessionAttributes") or ""
            ),
            "agotada": sesion.get("isSoldOut", False)
        })

    return sorted(sesiones, key=lambda s: s["fecha"])
