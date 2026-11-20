
# ==========================================
# INTEGRACIÓN DE KINÉPOLIS EN CINEDATA
# ==========================================


from collections import defaultdict

from scrapers import kinepolis as scraper

from procesamiento.normalizador_kinepolis import (
    normalizar_peliculas_kinepolis
)

from integracion.cadenas import (
    registrar_ubicaciones,
    registrar_cartelera
)


CADENA = "Kinépolis"


# ==========================================
# RELACIÓN ENTRE CINES Y CIUDADES
# ==========================================

CIUDAD_POR_CINE = {
    "KALIC": ("alicante", "Alicante"),
    "ESAMR": ("almeria", "Almería"),
    "PALZI": ("alzira", "Alzira"),
    "PFULL": ("barcelona", "Barcelona"),
    "KGRAN": ("granada", "Granada"),
    "KNEVA": ("granada", "Granada"),
    "ESMAR": ("marbella", "Marbella"),
    "KMAD": ("madrid", "Madrid"),
    "KALCO": ("madrid", "Madrid"),
    "ESMAT": ("mataro", "Mataró"),
    "KVAL": ("valencia", "Valencia")
}


# ==========================================
# AGRUPAR CINES POR CIUDAD
# ==========================================

def agrupar_cines_por_ciudad(cines):

    agrupados = defaultdict(list)

    for cine in cines:

        id_cine = cine.get("id")

        if id_cine not in CIUDAD_POR_CINE:
            raise ValueError(
                "No se ha configurado la ciudad "
                f"del cine: {id_cine}"
            )

        id_ciudad, nombre_ciudad = (
            CIUDAD_POR_CINE[id_cine]
        )

        agrupados[
            (id_ciudad, nombre_ciudad)
        ].append({
            "id": id_cine,
            "nombre": cine["nombre"]
        })

    ciudades = []

    for (id_ciudad, nombre_ciudad), lista_cines in agrupados.items():

        ciudades.append({
            "id": id_ciudad,
            "nombre": nombre_ciudad,
            "cines": sorted(
                lista_cines,
                key=lambda c: c["nombre"].casefold()
            )
        })

    return sorted(
        ciudades,
        key=lambda c: c["nombre"].casefold()
    )


# ==========================================
# INTEGRAR KINÉPOLIS
# ==========================================

def integrar_kinepolis():

    print("\n" + "=" * 50)
    print("          INTEGRACIÓN KINÉPOLIS")
    print("=" * 50)

    # Actualmente se utiliza el JSON local.
    if not scraper.URL_CARTELERA:
        print(
            "\nAVISO: Kinépolis utiliza una "
            "cartelera JSON guardada localmente."
        )

    # 1. Obtener cines desde el scraper
    cines = scraper.obtener_cines()

    if not cines:
        raise ValueError(
            "No se han encontrado cines Kinépolis."
        )

    # 2. Agrupar los cines por ciudad
    ciudades = agrupar_cines_por_ciudad(cines)

    # 3. Guardar ciudades y cines en SQLite
    total_ciudades, total_cines = registrar_ubicaciones(
        CADENA,
        ciudades
    )

    print("\nCiudades guardadas:", total_ciudades)
    print("Cines guardados:", total_cines)

    resumen = {
        "carteleras_guardadas": 0,
        "peliculas_procesadas": 0,
        "sin_peliculas": 0,
        "errores": 0
    }

    # 4. Procesar las películas de cada cine
    for cine in cines:

        print("\n" + "-" * 40)
        print("Cine:", cine["nombre"])

        try:
            originales = scraper.obtener_peliculas(
                cine["id"]
            )

            if not isinstance(originales, list):
                raise ValueError(
                    "El scraper no ha devuelto una lista."
                )

            # Evitar borrar carteleras antiguas por
            # falta de sesiones futuras en el JSON.
            if not originales:
                print(
                    "No hay películas futuras en "
                    "la fuente local."
                )

                resumen["sin_peliculas"] += 1
                continue

            # 5. Normalizar películas
            normalizadas = normalizar_peliculas_kinepolis(
                originales
            )

            if any(
                pelicula is None
                for pelicula in normalizadas
            ):
                raise ValueError(
                    "Hay películas sin identificador "
                    "o título válido."
                )

            # Evitar identificadores repetidos
            identificadores = [
                pelicula["id_externo"]
                for pelicula in normalizadas
            ]

            if len(identificadores) != len(set(identificadores)):
                raise ValueError(
                    "Hay identificadores duplicados."
                )

            # 6. Guardar cartelera en SQLite
            cantidad = registrar_cartelera(
                CADENA,
                cine["id"],
                cine["nombre"],
                normalizadas
            )

            resumen["carteleras_guardadas"] += 1
            resumen["peliculas_procesadas"] += cantidad

            print("Películas guardadas:", cantidad)

        except Exception as error:

            resumen["errores"] += 1

            print("ERROR:", error)
            print(
                "Se conservan los datos anteriores "
                "de este cine."
            )

    # ======================================
    # RESUMEN FINAL
    # ======================================

    print("\n" + "=" * 50)
    print("        RESUMEN DE KINÉPOLIS")
    print("=" * 50)

    print("Ciudades:", total_ciudades)
    print("Cines:", total_cines)

    print(
        "Carteleras guardadas:",
        resumen["carteleras_guardadas"]
    )

    print(
        "Películas procesadas:",
        resumen["peliculas_procesadas"]
    )

    print(
        "Cines sin películas futuras:",
        resumen["sin_peliculas"]
    )

    print("Errores:", resumen["errores"])

    return resumen


# ==========================================
# EJECUCIÓN INDEPENDIENTE
# ==========================================

if __name__ == "__main__":
    integrar_kinepolis()
