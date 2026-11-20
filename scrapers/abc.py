
import re
import requests
import time



from api.tmdb import buscar_pelicula_tmdb


# ==================================================
# CONFIGURACIÓN DE LOS CINES ABC
# ==================================================

CINES_ABC = {
    "ABC Park": {
        "subdominio": "abcpark",
        "recinto": 2
    },
    "ABC Saler": {
        "subdominio": "abcelsaler",
        "recinto": 172
    },
    "ABC Gran Turia": {
        "subdominio": "abcgranturia",
        "recinto": 171
    },
    "ABC Elx": {
        "subdominio": "abcelx",
        "recinto": 174
    },
    "ABC Gandía": {
        "subdominio": "abcgandia",
        "recinto": 173
    }
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9"
}


# ==================================================
# CONEXIÓN CON LA WEB
# ==================================================




def obtener_cartelera_json(cine):

    datos_cine = CINES_ABC[cine]

    subdominio = datos_cine["subdominio"]
    recinto = datos_cine["recinto"]

    url = f"https://{subdominio}.reservaentradas.com/{subdominio}/index"

    parametros = {
        "recinto": recinto,
        "key": "apirswebapp",
        "_": int(time.time() * 1_000_000)
    }

    respuesta = requests.get(
        url,
        params=parametros,
        headers=HEADERS,
        timeout=20
    )

    print("\n========== PETICIÓN CARTELERA ABC ==========")
    print("Cine:", cine)
    print("URL:", respuesta.url)
    print("Código HTTP:", respuesta.status_code)
    print("Tipo de contenido:", respuesta.headers.get("Content-Type"))

    respuesta.raise_for_status()

    datos = respuesta.json()

    print("Tipo de respuesta:", type(datos).__name__)

    if not isinstance(datos, dict):
        raise ValueError("La respuesta no es un objeto JSON.")

    if "Eventos" not in datos:
        raise ValueError(
            f"No se ha encontrado Eventos. "
            f"Claves recibidas: {list(datos.keys())}"
        )

    print("Eventos encontrados:", len(datos["Eventos"]))
    print("============================================")

    return datos

# ==================================================
# OBTENER ENLACES DE LAS PELÍCULAS
# ==================================================




# ==================================================
# BUSCAR INFORMACIÓN DENTRO DEL TEXTO
# ==================================================

def buscar_dato(texto, etiqueta):

    etiquetas = (
        r"DIRECTOR|REPARTO|G[ÉE]NERO|PA[ÍI]S|IDIOMA|DURACI[ÓO]N"
    )

    patron = (
        etiqueta
        + r"\s*:\s*(.*?)"
        + r"(?=\s+(?:" + etiquetas + r")\s*:|$)"
    )

    resultado = re.search(
        patron,
        texto,
        re.IGNORECASE
    )

    if resultado:
        return resultado.group(1).strip()

    return None


# ==================================================
# EXTRAER INFORMACIÓN DE UNA PELÍCULA
# ==================================================

def obtener_idiomas(evento, sesiones):
    idiomas = []

    # Información general de la película
    if evento.get("TieneVO") == 1:
        idiomas.append("Versión original")

    # Información específica de las sesiones
    for sesion in sesiones:
        formato = (sesion.get("formato") or "").upper()

        if "VOSE" in formato:
            idiomas.append("Versión original subtitulada en español")

        if "CAT" in formato:
            idiomas.append("Catalán")

    return list(dict.fromkeys(idiomas))


def extraer_cartelera(data, cine):

    lista_peliculas = []

    for evento in data.get("Eventos", []):


        titulo = evento.get("Titulo", "").strip()
        sinopsis = evento.get("Sinopsis")

        if sinopsis:
            sinopsis = re.sub(r"<[^>]+>", "", sinopsis)
            sinopsis = re.sub(r"\s+", " ", sinopsis).strip()
        else:
            sinopsis = "Sinopsis no disponible"
        # Ignorar eventos sin título
        if not titulo:
            continue

        # Ignorar contenidos que no sean películas
        if evento.get("EsPelicula") is False:
            continue

        # Consultar valoración en TMDB
        valoracion = None

        try:
            datos_tmdb = buscar_pelicula_tmdb(
                titulo,
                titulo,
                ""
            )

            if datos_tmdb:
                votos = datos_tmdb.get("vote_count", 0)

                if votos and votos > 0:
                    valoracion = {
                        "puntuacion": datos_tmdb.get("vote_average"),
                        "votos": votos
                    }

        except (requests.RequestException, RuntimeError, ValueError) as error:
            print("No se pudo consultar TMDB:", error)

        sesiones = []

        for sesion in evento.get("Sesiones", []):


            sesiones.append({
                "id": sesion.get("Id"),
                "fecha": sesion.get("FechaSesion"),
                "hora": sesion.get("Horatxt", "").strip(),
                "sala": sesion.get("Sala"),
                "formato": sesion.get("Formato"),


                "disponibles": sesion.get("Disponibles"),
                "aforo": sesion.get("Aforo"),
                "precio": sesion.get("PrecioUnico"),
                "compra_abierta": sesion.get("CompraAbierta")
            })

        pelicula = {
            "name": titulo,
            "originalName": evento.get("TituloOriginal"),
            "genre": evento.get("Genero"),
            "synopsis": sinopsis,
            "length": evento.get("Duracion"),
            "rating": evento.get("Calificacion"),
            "releaseDate": evento.get("Estreno"),
            "languages": obtener_idiomas(evento, sesiones),

            "formats": list(dict.fromkeys(
                [s.get("formato") for s in sesiones if s.get("formato")]
                + [
                    formato
                    for formato, disponible in [
                        ("IMAX", evento.get("TieneImax")),
                        ("REX", evento.get("TieneREX"))
                    ]
                    if disponible == 1
                ]
            )),
        }

        lista_peliculas.append(pelicula)

        lista_peliculas.append(pelicula)

        print("Película obtenida:", titulo)

    return lista_peliculas

# ==================================================
# FUNCIÓN PRINCIPAL DEL SCRAPER
# ==================================================

def obtener_peliculas(cine):

    if cine not in CINES_ABC:
        raise ValueError(
            "Debes seleccionar uno de estos cines: "
            + ", ".join(CINES_ABC.keys())
        )

    datos = obtener_cartelera_json(cine)

    lista_peliculas = extraer_cartelera(datos, cine)

    print(f"\nPelículas obtenidas de {cine}: {len(lista_peliculas)}")

    return lista_peliculas


# ==================================================
# PRUEBA DEL SCRAPER
# ==================================================

if __name__ == "__main__":

    print("\n========== SCRAPER CINESC ABC ==========\n")

    print("Selecciona un cine:\n")

    nombres = list(CINES_ABC.keys())

    for i, nombre in enumerate(nombres, 1):
        print(f"{i}. {nombre}")

    opcion = int(input("\nOpción: "))

    if 1 <= opcion <= len(nombres):

        cine = nombres[opcion - 1]

        peliculas = obtener_peliculas(cine)

        print(f"\n========== CARTELERA {cine.upper()} ==========\n")

        for pelicula in peliculas:
            print("\n========================================")
            print("TÍTULO:", pelicula["name"])
            print("TÍTULO ORIGINAL:", pelicula["originalName"])
            print("GÉNERO:", pelicula["genre"])
            print("SINOPSIS:", pelicula["synopsis"])
            print("DURACIÓN:", pelicula["length"], "minutos")
            print("CLASIFICACIÓN:", pelicula["rating"])
            print("FECHA DE ESTRENO:", pelicula["releaseDate"])
            print("IDIOMAS:", pelicula["languages"])
            print("FORMATOS:", pelicula["formats"])
            print("========================================")

        print("\nTotal de películas:", len(peliculas))

    else:
        print("Opción no válida.")
