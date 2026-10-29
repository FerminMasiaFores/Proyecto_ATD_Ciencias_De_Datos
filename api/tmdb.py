
import os
import re
import unicodedata

import requests
from dotenv import load_dotenv

load_dotenv()

URL = "https://api.themoviedb.org/3/search/movie"


def normalizar_titulo(titulo):
    texto = unicodedata.normalize("NFKD", titulo.casefold())

    texto = "".join(
        letra for letra in texto
        if not unicodedata.combining(letra)
    )

    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def buscar_pelicula_tmdb(titulo, titulo_original="", fecha_estreno=""):
    token = os.getenv("TMDB_READ_TOKEN")

    if not token:
        raise RuntimeError("Falta TMDB_READ_TOKEN en .env")

    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }

    params = {
        "query": titulo,
        "language": "es-ES",
        "include_adult": "false"
    }

    respuesta = requests.get(
        URL,
        headers=headers,
        params=params,
        timeout=15
    )

    respuesta.raise_for_status()

    resultados = respuesta.json().get("results", [])

    # Comparamos títulos normalizados
    titulos_buscados = {
        normalizar_titulo(t)
        for t in (titulo, titulo_original)
        if t
    }

    coincidencias = [
        pelicula
        for pelicula in resultados
        if (
            normalizar_titulo(pelicula.get("title") or "")
            in titulos_buscados
            or normalizar_titulo(pelicula.get("original_title") or "")
            in titulos_buscados
        )
    ]

    if len(coincidencias) == 1:
        return coincidencias[0]

    # Si hay varias películas con el mismo título,
    # intentamos distinguirlas por el año.
    if len(coincidencias) > 1 and fecha_estreno:
        anio = fecha_estreno[:4]

        por_anio = [
            p for p in coincidencias
            if (p.get("release_date") or "").startswith(anio)
        ]

        if len(por_anio) == 1:
            return por_anio[0]

    # Evitamos mostrar la valoración de otra película
    return None
