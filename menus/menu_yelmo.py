
import shutil
import textwrap
import requests

from scrapers.yelmo import obtener_cines, obtener_peliculas
from api.tmdb import buscar_pelicula_tmdb


# ==========================================
# SELECCIONAR OPCIÓN
# ==========================================

def seleccionar_opcion(cantidad):

    while True:
        respuesta = input("\nSelecciona una opción: ").strip()

        if respuesta.isdigit():
            opcion = int(respuesta)

            if 0 <= opcion <= cantidad:
                return opcion

        print("Opción no válida. Inténtalo de nuevo.")


# ==========================================
# FORMATO DE SINOPSIS
# ==========================================

def mostrar_sinopsis(sinopsis):

    ancho = min(
        shutil.get_terminal_size(
            fallback=(90, 24)
        ).columns - 4,
        90
    )

    ancho = max(30, ancho)

    for parrafo in sinopsis.splitlines():
        if parrafo.strip():
            print(textwrap.fill(parrafo, width=ancho))
        else:
            print()


# ==========================================
# INFORMACIÓN DE TMDB
# ==========================================

def mostrar_valoracion_tmdb(pelicula):

    print("\n--- VALORACIÓN TMDB ---\n")

    try:
        datos_tmdb = buscar_pelicula_tmdb(
            pelicula.get("name") or "",
            pelicula.get("originalName") or "",
            pelicula.get("releaseDate") or ""
        )

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

    except (requests.RequestException, RuntimeError, ValueError) as error:
        print("No se ha podido consultar TMDb.")
        print("Detalle:", error)


# ==========================================
# MOSTRAR FICHA DE PELÍCULA
# ==========================================

def mostrar_pelicula(pelicula):

    print("\n" + "=" * 50)
    print("          INFORMACIÓN DE LA PELÍCULA")
    print("=" * 50)

    generos = pelicula.get("genre") or []
    idiomas = pelicula.get("languages") or []
    formatos = pelicula.get("formats") or []

    titulo = pelicula.get("name") or "No disponible"
    titulo_original = pelicula.get("originalName") or "No disponible"
    duracion = pelicula.get("length") or "No disponible"
    clasificacion = pelicula.get("rating") or "No disponible"
    estreno = pelicula.get("releaseDate") or "No disponible"

    if estreno != "No disponible":
        estreno = estreno[:10]

    print("\nTítulo:", titulo)
    print("Título original:", titulo_original)
    print("Género:", ", ".join(generos) or "No disponible")
    print("Duración:", duracion)
    print("Clasificación por edades:", clasificacion)
    print("Fecha de estreno:", estreno)
    print("Idiomas:", ", ".join(idiomas) or "No disponible")
    print("Formatos:", ", ".join(formatos) or "No disponible")

    print("\n--- SINOPSIS ---\n")

    sinopsis = pelicula.get("synopsis") or "No disponible"
    mostrar_sinopsis(sinopsis)

    mostrar_valoracion_tmdb(pelicula)

    print("\n" + "=" * 50)


# ==========================================
# OBTENER PELÍCULAS DE UN CINE
# ==========================================

def cargar_peliculas(identificador):

    try:
        datos = obtener_peliculas(identificador)

        if not datos:
            print("No se han recibido datos de Yelmo.")
            return []

        if datos.get("errors"):
            print("Error GraphQL:", datos["errors"])
            return []

        resultado = (datos.get("data") or {}).get("movies") or {}

        return [
            elemento["node"]
            for elemento in resultado.get("edges", [])
            if elemento.get("node")
        ]

    except Exception as error:
        print("Error al consultar las películas:", error)
        return []


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

def main():

    print("\n" + "=" * 50)
    print("                    CINEDATA")
    print("=" * 50)

    print("\nCargando ciudades y cines Yelmo...")

    try:
        ciudades = obtener_cines()

    except Exception as error:
        print("No se han podido obtener los cines:", error)
        return

    if not ciudades:
        print("No se han encontrado ciudades disponibles.")
        return

    total_cines = sum(
        len(ciudad["cines"])
        for ciudad in ciudades
    )

    print(f"Ciudades encontradas: {len(ciudades)}")
    print(f"Cines encontrados: {total_cines}")

    # ======================================
    # MENÚ DE CIUDADES
    # ======================================

    while True:

        print("\n" + "=" * 50)
        print("              SELECCIONAR CIUDAD")
        print("=" * 50)

        for indice, ciudad in enumerate(ciudades, start=1):
            print(f"{indice}. {ciudad['nombre']}")

        print("\n0. Salir")

        opcion_ciudad = seleccionar_opcion(len(ciudades))

        if opcion_ciudad == 0:
            print("\n¡Hasta pronto!")
            break

        ciudad = ciudades[opcion_ciudad - 1]
        cines = ciudad["cines"]

        # ==================================
        # MENÚ DE CINES
        # ==================================

        while True:

            print("\n" + "=" * 50)
            print(f"CIUDAD: {ciudad['nombre']}")
            print("=" * 50)

            print("\n--- SELECCIONAR CINE ---\n")

            for indice, cine in enumerate(cines, start=1):
                print(f"{indice}. {cine['nombre']}")

            print("\n0. Volver a ciudades")

            opcion_cine = seleccionar_opcion(len(cines))

            if opcion_cine == 0:
                break

            cine = cines[opcion_cine - 1]

            print(f"\nConsultando películas de {cine['nombre']}...")

            peliculas = cargar_peliculas(cine["id"])

            if not peliculas:
                print("No se han encontrado películas para este cine.")
                continue

            # ==============================
            # MENÚ DE PELÍCULAS
            # ==============================

            while True:

                print("\n" + "=" * 50)
                print(f"CINE: {cine['nombre']}")
                print("=" * 50)

                print(
                    f"\n--- PELÍCULAS ENCONTRADAS "
                    f"({len(peliculas)}) ---\n"
                )

                for indice, pelicula in enumerate(
                    peliculas,
                    start=1
                ):
                    print(f"{indice}. {pelicula['name']}")

                print("\n0. Volver a cines")

                opcion_pelicula = seleccionar_opcion(
                    len(peliculas)
                )

                if opcion_pelicula == 0:
                    break

                pelicula = peliculas[opcion_pelicula - 1]

                mostrar_pelicula(pelicula)

                input(
                    "\nPulsa INTRO para volver "
                    "al listado de películas..."
                )


# ==========================================
# INICIAR CINEDATA
# ==========================================

if __name__ == "__main__":
    main()
