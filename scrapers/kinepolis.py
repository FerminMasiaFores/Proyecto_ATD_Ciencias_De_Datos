import requests
from bs4 import BeautifulSoup


URL = "https://www.yelmocines.es/cartelera/valencia/yelmo-cines-mercado-de-campanar"


def descargar_pagina():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/155.0.0.0 Safari/537.36"
        )
    }

    respuesta = requests.get(
        URL,
        headers=headers,
        timeout=15
    )

    print("Código HTTP:", respuesta.status_code)
    print("URL final:", respuesta.url)
    print("Tipo de contenido:", respuesta.headers.get("Content-Type"))

    return respuesta


def analizar_pagina(html):
    soup = BeautifulSoup(html, "html.parser")

    if soup.title:
        print("Título:", soup.title.get_text(strip=True))
    else:
        print("No se ha encontrado título.")

    return soup