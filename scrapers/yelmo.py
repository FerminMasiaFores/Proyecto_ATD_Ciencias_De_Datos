from curl_cffi import requests


URL = "https://api-g.cinepolis.com/v2/billboards/graphql"

API_KEY = "lQM6Mkvri1iHksKKCfpAiwGXq0YUZA7Nn6XAXRPr4i13LwXo"


QUERY = """
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


def obtener_peliculas(cine=""):

    headers = {
        "accept": "*/*",
        "accept-language": "es-ES,es;q=0.9",
        "content-type": "application/json",
        "country-id": "ES",
        "language": "ES",
        "origin": "https://cineyelmo.com",
        "priority": "u=1, i",
        "referer": "https://cineyelmo.com/",
        "sec-ch-ua": '"Not:A-Brand";v="8", "Chromium";v="156", "Google Chrome";v="156"',
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

    variables = {
        "category": "now-playing",
        "cinemas": cine,
        "limit": 100,
        "countryId": "ES",
        "isAbsoluteMediaPath": True
    }

    payload = {
        "operationName": "Movies",
        "query": QUERY,
        "variables": variables
    }

    respuesta = requests.post(
        URL,
        headers=headers,
        json=payload,
        timeout=20,
        impersonate="chrome"
    )

    print("Código HTTP:", respuesta.status_code)

    if respuesta.status_code != 200:
        print(respuesta.text)
        return None

    return respuesta.json()