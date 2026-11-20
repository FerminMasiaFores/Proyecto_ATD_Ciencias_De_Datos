
import socket
import json
import textwrap
import shutil


HOST = "127.0.0.1"
PORT = 5000


# ==========================================
# COMUNICACIÓN TCP
# ==========================================

def enviar_peticion(peticion):

    with socket.create_connection(
        (HOST, PORT),
        timeout=30
    ) as conexion:

        mensaje = json.dumps(
            peticion,
            ensure_ascii=False
        ) + "\n"

        conexion.sendall(mensaje.encode("utf-8"))

        with conexion.makefile(
            "r",
            encoding="utf-8"
        ) as entrada:
            respuesta = entrada.readline()

        if not respuesta:
            raise ConnectionError(
                "El servidor no ha respondido"
            )

        return json.loads(respuesta)


def solicitar_datos(accion, **parametros):

    peticion = {
        "accion": accion,
        **parametros
    }

    respuesta = enviar_peticion(peticion)

    if not respuesta.get("ok"):
        raise RuntimeError(
            respuesta.get("error", "Error desconocido")
        )

    return respuesta.get("datos")


# ==========================================
# SELECCIONAR OPCIÓN
# ==========================================

def seleccionar_opcion(cantidad):

    while True:

        respuesta = input(
            "\nSelecciona una opción: "
        ).strip()

        if respuesta.isdigit():

            opcion = int(respuesta)

            if 0 <= opcion <= cantidad:
                return opcion

        print("Opción no válida. Inténtalo de nuevo.")


# ==========================================
# MOSTRAR FICHA
# ==========================================

def mostrar_ficha(ficha):

    print("\n" + "=" * 50)
    print("           FICHA DE LA PELÍCULA")
    print("=" * 50)

    print("\nTítulo:", ficha.get("titulo") or "No disponible")

    print(
        "Título original:",
        ficha.get("titulo_original") or "No disponible"
    )

    generos = ficha.get("generos") or []

    print("Géneros:", ", ".join(generos) or "No disponible")

    print("Duración:", ficha.get("duracion") or "No disponible")

    print(
        "Clasificación:",
        ficha.get("clasificacion") or "No disponible"
    )

    print(
        "Estreno:",
        ficha.get("fecha_estreno") or "No disponible"
    )

    # SINOPSIS

    print("\n--- SINOPSIS ---\n")

    ancho = max(
        30,
        min(
            shutil.get_terminal_size(
                fallback=(90, 24)
            ).columns - 4,
            90
        )
    )

    sinopsis = ficha.get("sinopsis") or "No disponible"

    for parrafo in sinopsis.splitlines():

        if parrafo.strip():
            print(textwrap.fill(parrafo, width=ancho))
        else:
            print()

    # TMDB

    print("\n--- VALORACIÓN TMDB ---\n")

    tmdb = ficha.get("tmdb")

    if tmdb:

        votos = tmdb.get("votos") or 0
        valoracion = tmdb.get("valoracion")
        identificador = tmdb.get("id")

        if votos > 0 and valoracion is not None:

            print(f"Valoración: {valoracion:.1f}/10")
            print(f"Número de votos: {votos}")

        else:
            print("Esta película todavía no tiene valoraciones.")

        if identificador:
            print(
                "Ficha TMDb: "
                f"https://www.themoviedb.org/movie/{identificador}"
            )

    else:
        print("Valoración no disponible.")

    print("\n" + "=" * 50)


# ==========================================
# MENÚ DE PELÍCULAS
# ==========================================

def menu_peliculas(cadena, cine):

    peliculas = solicitar_datos(
        "listar_peliculas",
        cadena=cadena,
        id_cine=cine["id"]
    )

    if not peliculas:
        print("\nEste cine no tiene películas guardadas.")
        return

    while True:

        print("\n" + "=" * 50)
        print(f"CINE: {cine['nombre']}")
        print("=" * 50)

        print(f"\nPelículas encontradas: {len(peliculas)}\n")

        for i, pelicula in enumerate(peliculas, start=1):
            print(f"{i}. {pelicula['titulo']}")

        print("\n0. Volver a los cines")

        opcion = seleccionar_opcion(len(peliculas))

        if opcion == 0:
            break

        pelicula = peliculas[opcion - 1]

        ficha = solicitar_datos(
            "detalle_pelicula",
            cadena=cadena,
            id_cine=cine["id"],
            id_pelicula=pelicula["id"]
        )

        mostrar_ficha(ficha)

        input(
            "\nPulsa INTRO para volver "
            "al listado de películas..."
        )


# ==========================================
# MENÚ DE CINES
# ==========================================

def menu_cines(cadena, ciudad):

    cines = solicitar_datos(
        "listar_cines",
        cadena=cadena,
        id_ciudad=ciudad["id"]
    )

    if not cines:
        print("\nNo hay cines disponibles en esta ciudad.")
        return

    while True:

        print("\n" + "=" * 50)
        print(f"CIUDAD: {ciudad['nombre']}")
        print("=" * 50)

        print("\n--- SELECCIONAR CINE ---\n")

        for i, cine in enumerate(cines, start=1):
            print(f"{i}. {cine['nombre']}")

        print("\n0. Volver a las ciudades")

        opcion = seleccionar_opcion(len(cines))

        if opcion == 0:
            break

        cine = cines[opcion - 1]

        menu_peliculas(cadena, cine)


# ==========================================
# MENÚ DE CIUDADES
# ==========================================

def menu_ciudades(cadena):

    ciudades = solicitar_datos(
        "listar_ciudades",
        cadena=cadena
    )

    if not ciudades:
        print("\nNo hay ciudades disponibles para esta cadena.")
        return

    while True:

        print("\n" + "=" * 50)
        print(f"CADENA: {cadena}")
        print("=" * 50)

        print("\n--- SELECCIONAR CIUDAD ---\n")

        for i, ciudad in enumerate(ciudades, start=1):
            print(f"{i}. {ciudad['nombre']}")

        print("\n0. Volver a las cadenas")

        opcion = seleccionar_opcion(len(ciudades))

        if opcion == 0:
            break

        ciudad = ciudades[opcion - 1]

        menu_cines(cadena, ciudad)


# ==========================================
# MENÚ PRINCIPAL
# ==========================================

def main():

    print("\n" + "=" * 50)
    print("                    CINEDATA")
    print("=" * 50)

    try:

        cadenas = solicitar_datos("listar_cadenas")

        if not cadenas:
            print("\nNo hay cadenas almacenadas.")
            return

        while True:

            print("\n" + "=" * 50)
            print("          SELECCIONAR CADENA DE CINE")
            print("=" * 50)

            for i, cadena in enumerate(cadenas, start=1):
                print(f"{i}. {cadena}")

            print("\n0. Salir")

            opcion = seleccionar_opcion(len(cadenas))

            if opcion == 0:
                print("\n¡Hasta pronto!")
                break

            cadena = cadenas[opcion - 1]

            menu_ciudades(cadena)

    except (OSError, ValueError, RuntimeError) as error:

        print("\nSe ha producido un error:", error)
        print(
            "Comprueba que server.py esté funcionando "
            "y que la base de datos esté actualizada."
        )


if __name__ == "__main__":
    main()
