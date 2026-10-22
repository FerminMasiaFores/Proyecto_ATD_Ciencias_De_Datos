import requests
from bs4 import BeautifulSoup


URL = "https://www.yelmocines.es/cartelera/valencia/yelmo-cines-mercado-de-campanar"


def descargar_pagina():
    respuesta = requests.get(URL, timeout=15)

    print("Código HTTP:", respuesta.status_code)
    print("URL final:", respuesta.url)

    respuesta.raise_for_status()

    return respuesta.text


def guardar_html(html):
    with open(
        "datos/yelmo.html",
        "w",
        encoding="utf-8"
    ) as archivo:
        archivo.write(html)


def analizar_pagina(html):
    soup = BeautifulSoup(html, "html.parser")

    print("\nTítulo de la página:")
    print(soup.title.get_text(strip=True))

    print("\n--- H1 ---")
    for elemento in soup.find_all("h1"):
        texto = elemento.get_text(" ", strip=True)
        if texto:
            print(texto)

    print("\n--- H2 ---")
    for elemento in soup.find_all("h2"):
        texto = elemento.get_text(" ", strip=True)
        if texto:
            print(texto)

    print("\n--- H3 ---")
    for elemento in soup.find_all("h3"):
        texto = elemento.get_text(" ", strip=True)
        if texto:
            print(texto)

    print("\n--- H4 ---")
    for elemento in soup.find_all("h4"):
        texto = elemento.get_text(" ", strip=True)
        if texto:
            print(texto)

    return soup