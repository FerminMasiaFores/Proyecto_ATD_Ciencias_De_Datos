import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import requests
import os
import tempfile


# ==========================================
# CONFIGURACIÓN
# ==========================================

# Kinépolis no tiene un enlace aparte para la cartelera: las sesiones
# y las películas van metidas dentro del HTML de la página principal,
# en el script "jQuery.extend(Drupal.settings, {...})".
# Si la descarga falla, se usa el JSON guardado en la carpeta datos.
URL_CARTELERA = "https://kinepolis.es/"

# Texto que marca dónde empiezan los datos dentro del HTML
# (en la página hay varios Drupal.settings, solo uno los lleva)
MARCADOR = '"current_movies":'

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/156.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9"
}

ARCHIVO_LOCAL = (
    Path(__file__).resolve().parent.parent
    / "datos" / "kinepolis_cartelera.json"
)

# Aquí se guarda la cartelera para no leerla cada vez
_cartelera = None


# ==========================================
# CARGAR LA CARTELERA
# ==========================================

def _extraer_cartelera(html):

    # Buscar dónde empiezan los datos y la llave "{" que los abre.
    # Si no está, index() lanza ValueError.
    inicio = html.index("{", html.index(MARCADOR))

    # raw_decode lee un único objeto JSON desde esa posición
    # y se para donde termina, sin tener que buscar el cierre
    datos, _ = json.JSONDecoder().raw_decode(html, inicio)

    return datos


def _descargar_cartelera():

    print("Descargando la cartelera de", URL_CARTELERA)

    respuesta = requests.get(URL_CARTELERA, headers=HEADERS, timeout=30)

    print("Código HTTP (Kinépolis):", respuesta.status_code)

    respuesta.raise_for_status()

    return _extraer_cartelera(respuesta.text)



# ==========================================
# GUARDAR COPIA LOCAL DE FORMA SEGURA
# ==========================================

def _guardar_archivo_local(datos):

    ARCHIVO_LOCAL.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    archivo_temporal = None

    try:
        # Escribir primero en un archivo temporal.
        # Así no dañamos el JSON anterior si
        # se interrumpe la escritura.

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=ARCHIVO_LOCAL.parent,
            suffix=".tmp",
            delete=False
        ) as archivo:

            archivo_temporal = Path(archivo.name)

            json.dump(
                datos,
                archivo,
                ensure_ascii=False
            )

        # Sustituir el JSON anterior solo cuando
        # el archivo nuevo está completamente escrito.
        os.replace(
            archivo_temporal,
            ARCHIVO_LOCAL
        )

    finally:

        if (
            archivo_temporal is not None
            and archivo_temporal.exists()
        ):
            archivo_temporal.unlink()



def _leer_archivo_local():

    print("Usando el archivo local:", ARCHIVO_LOCAL.name)

    with open(ARCHIVO_LOCAL, encoding="utf-8") as f:
        return json.load(f)


# ==========================================
# VALIDAR DATOS DESCARGADOS
# ==========================================

def _validar_cartelera(datos):

    if not isinstance(datos, dict):
        raise ValueError(
            "La cartelera no es un diccionario."
        )

    peliculas = datos.get("films")
    sesiones = datos.get("sessions")

    if not isinstance(peliculas, list):
        raise ValueError(
            "Falta la lista de películas."
        )

    if not isinstance(sesiones, list):
        raise ValueError(
            "Falta la lista de sesiones."
        )

    if not peliculas:
        raise ValueError(
            "La descarga no contiene películas."
        )

    if not sesiones:
        raise ValueError(
            "La descarga no contiene sesiones."
        )

    # Verificar que los datos tienen una
    # estructura reconocible.

    peliculas_validas = any(
        isinstance(pelicula, dict)
        and pelicula.get("id")
        and pelicula.get("title")
        for pelicula in peliculas
    )

    sesiones_validas = any(
        isinstance(sesion, dict)
        and sesion.get("showtime")
        and sesion.get("complexOperator")
        for sesion in sesiones
    )

    if not peliculas_validas or not sesiones_validas:
        raise ValueError(
            "La cartelera tiene una estructura inválida."
        )

    return {
        "peliculas": peliculas,
        "sesiones": sesiones
    }


# ==========================================
# FORZAR ACTUALIZACIÓN DESDE LA WEB
# ==========================================

def actualizar_cartelera():

    global _cartelera

    print("\nActualizando cartelera Kinépolis...")

    # Descargar desde la web sin utilizar
    # la memoria caché ni el JSON local.
    datos = _descargar_cartelera()

    # Validar antes de sustituir nada.
    cartelera_nueva = _validar_cartelera(
        datos
    )

    # Guardar la nueva copia local.
    _guardar_archivo_local(datos)

    # Actualizar los datos en memoria.
    _cartelera = cartelera_nueva

    print("Cartelera Kinépolis actualizada.")

    print(
        "Películas:",
        len(_cartelera["peliculas"])
    )

    print(
        "Sesiones:",
        len(_cartelera["sesiones"])
    )

    return _cartelera



# ==========================================
# CARGAR CARTELERA CON RESPALDO LOCAL
# ==========================================

def cargar_cartelera():

    global _cartelera

    # 1. Reutilizar los datos de memoria
    # si ya están cargados.
    if _cartelera is not None:
        return _cartelera

    # 2. Intentar una descarga nueva.
    try:
        return actualizar_cartelera()

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        OSError
    ) as error:

        print(
            "\nNo se pudo actualizar Kinépolis:",
            error
        )

        print(
            "Intentando utilizar la última "
            "copia local..."
        )

    # 3. Utilizar el respaldo si falla la web.
    datos = _leer_archivo_local()

    _cartelera = _validar_cartelera(
        datos
    )

    print("Cartelera cargada desde el respaldo.")

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



# ==========================================
# FECHAS Y HORAS DE LAS SESIONES
# ==========================================

ZONA_HORARIA = ZoneInfo("Europe/Madrid")


def _hora_sesion(sesion):

    # Kinépolis proporciona fechas con zona horaria.
    texto = sesion["showtime"].replace(
        "Z",
        "+00:00"
    )

    fecha = datetime.fromisoformat(texto)

    if fecha.tzinfo is None:
        raise ValueError(
            "La sesión no tiene información "
            "de zona horaria."
        )

    # Convertir a la hora española
    return fecha.astimezone(ZONA_HORARIA)


def _sesiones_futuras(cine):

    ahora = datetime.now(ZONA_HORARIA)

    sesiones = cargar_cartelera()["sesiones"]

    return [
        sesion
        for sesion in sesiones
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
