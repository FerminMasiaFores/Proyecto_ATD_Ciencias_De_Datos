
import textwrap
import shutil

from scrapers.yelmo import obtener_peliculas


CINES = {
    "Mercado de Campanar (Valencia)": "mercado-de-campanar-valencia",
    "VidaNova Parc (Valencia)": "vidanova-parc-valencia",
    "La Vaguada (Madrid)": "la-vaguada-madrid",
    "Premium Alisios (Las Palmas)": "premium-alisios-las-palmas",
    "Bahía Sur (Cádiz)": "premium-bahia-sur-cadiz"
}


def seleccionar_opcion(cantidad):
    while True:
        respuesta = input("\nSelecciona una opción: ").strip()

        if respuesta.isdigit():
            opcion = int(respuesta)

            if 0 <= opcion <= cantidad:
                return opcion

        print("Opción no válida. Inténtalo de nuevo.")


def mostrar_pelicula(pelicula):
    print("\n" + "=" * 45)
    print("          INFORMACIÓN DE LA PELÍCULA")
    print("=" * 45)

    generos = pelicula.get("genre") or []
    idiomas = pelicula.get("languages") or []
    formatos = pelicula.get("formats") or []

    print("Título:", pelicula.get("name") or "No disponible")
    print("Título original:", pelicula.get("originalName") or "No disponible")
    print("Género:", ", ".join(generos) or "No disponible")
    print("Duración:", pelicula.get("length") or "No disponible")
    print("Clasificación:", pelicula.get("rating") or "No disponible")
    print("Estreno:", pelicula.get("releaseDate") or "No disponible")
    print("Idiomas:", ", ".join(idiomas) or "No disponible")
    print("Formatos:", ", ".join(formatos) or "No disponible")

    print("\n--- SINOPSIS ---\n")

    sinopsis = pelicula.get("synopsis") or "No disponible"

    # Detectar el ancho de la terminal
    ancho = min(
        shutil.get_terminal_size(fallback=(90, 24)).columns - 4,
        90
    )
    ancho = max(30, ancho)

    # Dividir la sinopsis en líneas legibles
    for parrafo in sinopsis.splitlines():
        if parrafo.strip():
            print(textwrap.fill(parrafo, width=ancho))
        else:
            print()

    print("\nValoración TMDb: pendiente de integrar")
    print("=" * 45)


def main():
    while True:
        print("\n" + "=" * 45)
        print("                  CINEDATA")
        print("=" * 45)

        nombres_cines = list(CINES.keys())

        print("\n--- SELECCIONAR CINE ---")

        for indice, nombre in enumerate(nombres_cines, start=1):
            print(f"{indice}. {nombre}")

        print("0. Salir")

        opcion_cine = seleccionar_opcion(len(nombres_cines))

        if opcion_cine == 0:
            print("\n¡Hasta pronto!")
            break

        nombre_cine = nombres_cines[opcion_cine - 1]
        identificador = CINES[nombre_cine]

        print(f"\nConsultando películas de {nombre_cine}...")

        datos = obtener_peliculas(identificador)

        if not datos:
            print("No se han podido obtener las películas.")
            continue

        if datos.get("errors"):
            print("Error GraphQL:", datos["errors"])
            continue

        resultado = (datos.get("data") or {}).get("movies") or {}

        peliculas = [
            elemento["node"]
            for elemento in resultado.get("edges", [])
            if elemento.get("node")
        ]

        if not peliculas:
            print("No se han encontrado películas.")
            continue

        # Menú de películas
        while True:
            print("\n" + "=" * 45)
            print(f"CINE: {nombre_cine}")
            print("=" * 45)

            print("\n--- PELÍCULAS DISPONIBLES ---")

            for indice, pelicula in enumerate(peliculas, start=1):
                print(f"{indice}. {pelicula['name']}")

            print("\n0. Volver a seleccionar cine")

            opcion_pelicula = seleccionar_opcion(len(peliculas))

            if opcion_pelicula == 0:
                break

            pelicula = peliculas[opcion_pelicula - 1]

            mostrar_pelicula(pelicula)

            input("\nPulsa INTRO para volver a las películas...")


if __name__ == "__main__":
    main()
