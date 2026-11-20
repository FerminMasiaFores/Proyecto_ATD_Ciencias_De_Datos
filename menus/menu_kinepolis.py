
import requests

from scrapers.kinepolis import (
    obtener_cines,
    obtener_peliculas
)
from api.tmdb import buscar_pelicula_tmdb

# Reutilizamos las funciones que ya hay en el menú de Yelmo
from menus.menu_yelmo import (
    seleccionar_opcion,
    mostrar_sinopsis
)


# ==========================================
# BUSCAR LA PELÍCULA EN TMDB
# ==========================================

def buscar_en_tmdb(pelicula):

    # Kinépolis pone "VOSE" delante del título de las
    # versiones originales; para TMDb lo quitamos.
    titulo = pelicula["titulo"]

    if titulo.upper().startswith("VOSE "):
        titulo = titulo[5:]

    try:
        return buscar_pelicula_tmdb(titulo, "", pelicula["estreno"])

    except (requests.RequestException, RuntimeError, ValueError) as error:
        print("No se ha podido consultar TMDb:", error)
        return None


def mostrar_valoracion(datos_tmdb):

    print("\n--- VALORACIÓN TMDB ---\n")

    if datos_tmdb is None:
        print("No se ha encontrado una coincidencia fiable.")
        return

    valoracion = datos_tmdb.get("vote_average") or 0
    votos = datos_tmdb.get("vote_count") or 0
    identificador = datos_tmdb.get("id")

    if votos > 0:
        print(f"Valoración: {valoracion:.1f}/10")
        print(f"Número de votos: {votos}")
    else:
        print("Esta película todavía no tiene valoraciones.")

    if identificador:
        print(
            "Ficha TMDb: "
            f"https://www.themoviedb.org/movie/{identificador}"
        )


# ==========================================
# MOSTRAR FICHA DE PELÍCULA
# ==========================================

def mostrar_pelicula(pelicula):

    # Kinépolis no da el título original: lo sacamos de TMDb
    datos_tmdb = buscar_en_tmdb(pelicula)

    titulo_original = (
        (datos_tmdb or {}).get("original_title")
        or "No disponible"
    )

    print("\n" + "=" * 50)
    print("          INFORMACIÓN DE LA PELÍCULA")
    print("=" * 50)

    duracion = pelicula["duracion"]

    print("\nTítulo:", pelicula["titulo"])
    print("Título original:", titulo_original)
    print("Género:", ", ".join(pelicula["generos"]) or "No disponible")
    print(
        "Duración:",
        f"{duracion} min" if duracion else "No disponible"
    )
    print("Clasificación por edades:", pelicula["edad"] or "No disponible")
    print("Fecha de estreno:", pelicula["estreno"] or "No disponible")
    print("Idioma:", pelicula["idioma"] or "No disponible")
    print("Formatos:", ", ".join(pelicula["formatos"]) or "No disponible")

    print("\n--- SINOPSIS ---\n")

    mostrar_sinopsis(pelicula["sinopsis"] or "No disponible")

    mostrar_valoracion(datos_tmdb)

    print("\n" + "=" * 50)


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

def main():

    print("\n" + "=" * 50)
    print("                  KINÉPOLIS")
    print("=" * 50)

    print("\nCargando cines Kinépolis...")

    try:
        cines = obtener_cines()

    except (OSError, ValueError, KeyError) as error:
        print("No se han podido obtener los cines:", error)
        return

    if not cines:
        print("No se han encontrado cines disponibles.")
        return

    print(f"Cines encontrados: {len(cines)}")

    # ======================================
    # MENÚ DE CINES
    # ======================================

    while True:

        print("\n" + "=" * 50)
        print("               SELECCIONAR CINE")
        print("=" * 50 + "\n")

        for indice, cine in enumerate(cines, start=1):
            print(f"{indice}. {cine['nombre']}")

        print("\n0. Volver al menú principal")

        opcion_cine = seleccionar_opcion(len(cines))

        if opcion_cine == 0:
            break

        cine = cines[opcion_cine - 1]

        peliculas = obtener_peliculas(cine["id"])

        if not peliculas:
            print("No quedan sesiones en este cine.")
            continue

        # ==================================
        # MENÚ DE PELÍCULAS
        # ==================================

        while True:

            print("\n" + "=" * 50)
            print(f"CINE: {cine['nombre']}")
            print("=" * 50)

            print(
                f"\n--- PELÍCULAS ENCONTRADAS "
                f"({len(peliculas)}) ---\n"
            )

            for indice, pelicula in enumerate(peliculas, start=1):
                print(f"{indice}. {pelicula['titulo']}  ")

            print("\n0. Volver a cines")

            opcion_pelicula = seleccionar_opcion(len(peliculas))

            if opcion_pelicula == 0:
                break

            pelicula = peliculas[opcion_pelicula - 1]

            mostrar_pelicula(pelicula)

            input(
                "\nPulsa INTRO para volver "
                "al listado de películas..."
            )


# ==========================================
# INICIAR KINÉPOLIS
# ==========================================

if __name__ == "__main__":
    main()
