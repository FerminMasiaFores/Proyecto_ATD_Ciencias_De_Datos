
from collections import defaultdict

from scrapers import abc as scraper

from procesamiento.normalizador_abc import (
    normalizar_peliculas_abc
)

from integracion.cadenas import (
    registrar_ubicaciones,
    registrar_cartelera
)


# ==========================================
# CONFIGURACIÓN
# ==========================================

CADENA = "ABC"

CIUDADES_ABC = {
    "ABC Park": ("valencia", "Valencia"),
    "ABC Saler": ("valencia", "Valencia"),
    "ABC Gran Turia": ("xirivella", "Xirivella"),
    "ABC Elx": ("elche", "Elche"),
    "ABC Gandía": ("gandia", "Gandía")
}


# ==========================================
# OBTENER CIUDADES Y CINES
# ==========================================

def obtener_ubicaciones_abc():

    agrupados = defaultdict(list)

    for nombre, datos in scraper.CINES_ABC.items():

        if nombre not in CIUDADES_ABC:
            raise ValueError(
                f"Ciudad no configurada para {nombre}"
            )

        id_ciudad, nombre_ciudad = (
            CIUDADES_ABC[nombre]
        )

        id_cine = datos["subdominio"]

        agrupados[
            (id_ciudad, nombre_ciudad)
        ].append({
            "id": id_cine,
            "nombre": nombre
        })

    ciudades = []

    for (id_ciudad, nombre_ciudad), cines in agrupados.items():

        ciudades.append({
            "id": id_ciudad,
            "nombre": nombre_ciudad,
            "cines": sorted(
                cines,
                key=lambda c: c["nombre"].casefold()
            )
        })

    return sorted(
        ciudades,
        key=lambda c: c["nombre"].casefold()
    )


# ==========================================
# INTEGRAR CINES ABC
# ==========================================

def integrar_abc():

    print("\n" + "=" * 50)
    print("          INTEGRACIÓN CINES ABC")
    print("=" * 50)

    # 1. Guardar ciudades y cines
    ciudades = obtener_ubicaciones_abc()

    total_ciudades, total_cines = registrar_ubicaciones(
        CADENA,
        ciudades
    )

    print("\nCiudades guardadas:", total_ciudades)
    print("Cines registrados:", total_cines)

    resumen = {
        "correctas": 0,
        "sin_peliculas": 0,
        "errores": 0,
        "peliculas_procesadas": 0
    }

    # 2. Recorrer los cines ABC
    for nombre_cine, datos_cine in scraper.CINES_ABC.items():

        print("\n" + "-" * 45)
        print("Actualizando:", nombre_cine)

        id_cine = datos_cine["subdominio"]

        try:

            # Obtener películas mediante el scraper
            originales = scraper.obtener_peliculas(
                nombre_cine
            )

            if not isinstance(originales, list):
                raise ValueError(
                    "El scraper no ha devuelto una lista."
                )

            # Una respuesta vacía puede ser temporal.
            # No borrar datos anteriores sin confirmación.
            if not originales:

                print(
                    "No se han obtenido películas. "
                    "Se conservan los datos anteriores."
                )

                resumen["sin_peliculas"] += 1
                continue

            # 3. Normalizar
            normalizadas = normalizar_peliculas_abc(
                originales
            )

            if not normalizadas:
                raise ValueError(
                    "No hay películas válidas."
                )

            print(
                "Películas normalizadas:",
                len(normalizadas)
            )

            # 4. Guardar en SQLite
            cantidad = registrar_cartelera(
                CADENA,
                id_cine,
                nombre_cine,
                normalizadas
            )

            resumen["correctas"] += 1
            resumen["peliculas_procesadas"] += cantidad

            print(
                "Películas guardadas:",
                cantidad
            )

        except Exception as error:

            resumen["errores"] += 1

            print(
                "ERROR al actualizar:",
                nombre_cine
            )

            print("Detalle:", error)

            print(
                "Se conserva la cartelera anterior."
            )

    # ======================================
    # RESUMEN
    # ======================================

    print("\n" + "=" * 50)
    print("        RESUMEN INTEGRACIÓN ABC")
    print("=" * 50)

    print(
        "Cines actualizados:",
        resumen["correctas"]
    )

    print(
        "Cines sin películas:",
        resumen["sin_peliculas"]
    )

    print(
        "Cines con errores:",
        resumen["errores"]
    )

    print(
        "Películas procesadas:",
        resumen["peliculas_procesadas"]
    )

    return resumen


# ==========================================
# EJECUCIÓN INDEPENDIENTE
# ==========================================

if __name__ == "__main__":
    integrar_abc()
