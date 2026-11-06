
import os
from pathlib import Path

from curl_cffi import requests
from dotenv import load_dotenv


# ==========================================
# CONFIGURACIÓN DE LA API
# ==========================================

# Cargar el archivo .env desde la raíz del proyecto
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.getenv("YELMO_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "No se ha encontrado YELMO_API_KEY en el archivo .env"
    )


# Endpoints GraphQL

URL_PELICULAS = (
    "https://api-g.cinepolis.com/v2/billboards/graphql"
)

URL_CINES = (
    "https://api-g.cinepolis.com/shared-services/locations/graphql"
)


# ==========================================
# CONSULTA GRAPHQL DE PELÍCULAS
# ==========================================

QUERY_MOVIES = """
query Movies(
    $countryId: String!,
    $category: String,
    $cinemas: String,
    $after: String,
    $limit: Int,
    $isAbsoluteMediaPath: Boolean
) {
    movies(
        countryId: $countryId
        category: $category
        cinemas: $cinemas
        after: $after
        limit: $limit
        isAbsoluteMediaPath: $isAbsoluteMediaPath
    ) {
        pageInfo {
            startCursor
            endCursor
            hasNextPage
            hasPreviousPage
        }
        totalCount
        edges {
            cursor
            node {
                id
                type
                countryId
                name
                originalName
                distributor
                rating
                ratingDescription
                position
                genre
                synopsis
                length
                availableForSale
                releaseDate
                languages
                formats
                cities
                cinemas
                categories
                media {
                    resource
                    type
                    code
                    sizes {
                        large
                        medium
                        small
                    }
                }
                experiences {
                    icon
                    name
                }
            }
        }
    }
}
"""


# ==========================================
# CONSULTA GRAPHQL DE CIUDADES Y CINES
# ==========================================

QUERY_CITIES = """
query Cities($countryId: String!) {
    cities(country_id: $countryId) {
        edges {
            node {
                id
                name
                regions {
                    regionId
                    regionName
                }
                settings {
                    hasFoodSales
                    hasPresales
                }
                timezone
                cinemas {
                    id
                    regionId
                    vistaId
                    type
                    name
                    cityId
                    lat
                    lng
                    alias
                    businessType
                    experiences {
                        icon
                        name
                    }
                    settings {
                        requireContiguousSeating
                    }
                }
            }
        }
    }
}
"""


# ==========================================
# FUNCIÓN GENERAL PARA CONSULTAR GRAPHQL
# ==========================================

def _consultar_graphql(
    payload,
    descripcion,
    url=URL_PELICULAS
):

    headers = {
        "accept": "*/*",
        "accept-language": "es-ES,es;q=0.9",
        "content-type": "application/json",
        "country-id": "ES",
        "language": "ES",
        "origin": "https://cineyelmo.com",
        "priority": "u=1, i",
        "referer": "https://cineyelmo.com/",
        "sec-ch-ua": (
            '"Not:A-Brand";v="8", '
            '"Chromium";v="156", '
            '"Google Chrome";v="156"'
        ),
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/156.0.0.0 Safari/537.36"
        ),
        "x-apikey": API_KEY
    }

    respuesta = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=20,
        impersonate="chrome"
    )

    print(
        f"Código HTTP ({descripcion}):",
        respuesta.status_code
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    if datos.get("errors"):
        raise ValueError(
            f"Error GraphQL: {datos['errors']}"
        )

    return datos


# ==========================================
# OBTENER PELÍCULAS DE UN CINE
# ==========================================

def obtener_peliculas(cine=""):

    variables = {
        "category": "now-playing",
        "cinemas": cine,
        "limit": 100,
        "countryId": "ES",
        "isAbsoluteMediaPath": True
    }

    payload = {
        "operationName": "Movies",
        "query": QUERY_MOVIES,
        "variables": variables
    }

    return _consultar_graphql(
        payload,
        "películas",
        URL_PELICULAS
    )


# ==========================================
# OBTENER TODAS LAS CIUDADES Y CINES YELMO
# ==========================================

def obtener_cines():

    payload = {
        "operationName": "Cities",
        "query": QUERY_CITIES,
        "variables": {
            "countryId": "ES"
        }
    }

    # Usar el endpoint de localizaciones
    datos = _consultar_graphql(
        payload,
        "cines",
        URL_CINES
    )

    edges = (
        (datos.get("data") or {})
        .get("cities", {})
        .get("edges", [])
    )

    ciudades = []

    for elemento in edges:

        ciudad = elemento.get("node") or {}

        cines = []

        for cine in ciudad.get("cinemas") or []:

            if not cine.get("id") or not cine.get("name"):
                continue

            cines.append({
                "id": cine["id"],
                "nombre": cine["name"]
            })

        # Guardar solo ciudades que tengan cines
        if cines:

            ciudades.append({
                "id": ciudad.get("id", ""),
                "nombre": ciudad.get(
                    "name",
                    "Sin nombre"
                ),
                "cines": sorted(
                    cines,
                    key=lambda c: c["nombre"].casefold()
                )
            })

    # Ordenar las ciudades alfabéticamente
    return sorted(
        ciudades,
        key=lambda c: c["nombre"].casefold()
    )
