
import time

from scrapers.yelmo import (
    obtener_cines,
    obtener_peliculas
)

from procesamiento.normalizador import (
    normalizar_peliculas_yelmo
)

from integracion.cadenas import (
    registrar_ubicaciones,
    registrar_cartelera
)

from almacenamiento.database import (
    conectar,
    crear_tablas
)


CADENA = "Yelmo"

# Intervalo entre actualizaciones correctas
HORAS_ACTUALIZACION = 24

# Tiempo para reintentar una descarga fallida
MINUTOS_REINTENTO = 30

# Pausa entre peticiones a Yelmo
PAUSA_PETICIONES = 1


# ==========================================
# CREAR TABLA DE CONTROL
# ==========================================

def crear_tabla_control():

    conexion = conectar()

    try:
        with conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS
                control_actualizaciones_cine (
                    cadena TEXT NOT NULL,
                    id_cine TEXT NOT NULL,
                    ultimo_intento INTEGER,
                    ultimo_exito INTEGER,
                    estado TEXT NOT NULL,
                    detalle TEXT,

                    PRIMARY KEY (cadena, id_cine)
                )
            """)

    finally:
        conexion.close()


# ==========================================
# CONSULTAR ESTADO DE UN CINE
# ==========================================

def consultar_estado(id_cine):

    conexion = conectar()

    try:
        return conexion.execute("""
            SELECT
                ultimo_intento,
                ultimo_exito,
                estado

            FROM control_actualizaciones_cine

            WHERE cadena = ?
            AND id_cine = ?
        """, (CADENA, id_cine)).fetchone()

    finally:
        conexion.close()


# ==========================================
# REGISTRAR RESULTADO DE ACTUALIZACIÓN
# ==========================================

def registrar_estado(id_cine, estado, detalle="", exito=False):

    ahora = int(time.time())

    ultimo_exito = ahora if exito else None

    conexion = conectar()

    try:
        with conexion:
            conexion.execute("""
                INSERT INTO control_actualizaciones_cine (
                    cadena,
                    id_cine,
                    ultimo_intento,
                    ultimo_exito,
                    estado,
                    detalle
                )

                VALUES (?, ?, ?, ?, ?, ?)

                ON CONFLICT(cadena, id_cine)
                DO UPDATE SET

                    ultimo_intento = excluded.ultimo_intento,

                    ultimo_exito = COALESCE(
                        excluded.ultimo_exito,
                        control_actualizaciones_cine.ultimo_exito
                    ),

                    estado = excluded.estado,
                    detalle = excluded.detalle

            """, (
                CADENA,
                id_cine,
                ahora,
                ultimo_exito,
                estado,
                detalle
            ))

    finally:
        conexion.close()


# ==========================================
# COMPROBAR SI UN CINE NECESITA ACTUALIZACIÓN
# ==========================================

def necesita_actualizacion(id_cine):

    estado = consultar_estado(id_cine)

    if estado is None:
        return True

    ultimo_intento, ultimo_exito, resultado = estado

    ahora = int(time.time())

    # Si la última descarga correcta es reciente,
    # no necesitamos descargar nuevamente.
    if ultimo_exito is not None:

        intervalo = HORAS_ACTUALIZACION * 3600

        if ahora - ultimo_exito < intervalo:
            return False

    # Si falló recientemente, esperar al reintento.
    if resultado == "error" and ultimo_intento is not None:

        intervalo = MINUTOS_REINTENTO * 60

        if ahora - ultimo_intento < intervalo:
            return False

    return True


# ==========================================
# ACTUALIZAR UN CINE
# ==========================================

def actualizar_cine(cine):

    id_cine = cine["id"]
    nombre_cine = cine["nombre"]

    print(f"\nCine: {nombre_cine}")

    if not necesita_actualizacion(id_cine):
        print("Actualización no necesaria todavía.")
        return "omitido"

    try:
        datos = obtener_peliculas(id_cine)

        if not isinstance(datos, dict):
            raise ValueError("Respuesta de API no válida.")

        if datos.get("errors"):
            raise ValueError(
                f"Error GraphQL: {datos['errors']}"
            )

        resultado = (datos.get("data") or {}).get("movies")

        if not isinstance(resultado, dict):
            raise ValueError(
                "La API no ha devuelto una cartelera válida."
            )

        # Comprobar que no hay páginas pendientes
        pagina = resultado.get("pageInfo") or {}

        if pagina.get("hasNextPage"):
            raise ValueError(
                "Hay páginas pendientes de descargar."
            )

        edges = resultado.get("edges")
        total_api = resultado.get("totalCount")

        if not isinstance(edges, list):
            raise ValueError("Falta la lista de películas.")

        if not isinstance(total_api, int):
            raise ValueError("Falta el total de películas.")

        if total_api != len(edges):
            raise ValueError(
                "La descarga está incompleta."
            )

        peliculas = [
            elemento["node"]
            for elemento in edges
            if isinstance(elemento, dict)
            and isinstance(elemento.get("node"), dict)
        ]

        if len(peliculas) != len(edges):
            raise ValueError(
                "Existen películas sin datos válidos."
            )

        # Normalizar
        normalizadas = normalizar_peliculas_yelmo(
            peliculas
        )

        if len(normalizadas) != len(peliculas):
            raise ValueError(
                "Normalización incompleta."
            )

        # Guardar en SQLite
        cantidad = registrar_cartelera(
            CADENA,
            id_cine,
            nombre_cine,
            normalizadas
        )

        # Distinguir cartelera vacía de error
        if total_api == 0:

            registrar_estado(
                id_cine,
                "vacia",
                "La API confirma cero películas.",
                exito=True
            )

            print("Cartelera vacía confirmada.")
            return "vacia"

        registrar_estado(
            id_cine,
            "correcto",
            f"{cantidad} películas guardadas.",
            exito=True
        )

        print(f"Películas guardadas: {cantidad}")
        return "correcto"

    except Exception as error:

        print("Error actualizando el cine:", error)

        registrar_estado(
            id_cine,
            "error",
            str(error),
            exito=False
        )

        return "error"


# ==========================================
# ACTUALIZACIÓN GENERAL DE YELMO
# ==========================================

def actualizar_yelmo(solo_valencia=False):

    print("\n" + "=" * 50)
    print("       ACTUALIZACIÓN DE CINEDATA")
    print("=" * 50)

    crear_tablas()
    crear_tabla_control()

    print("\nConsultando ciudades y cines...")

    try:
        ciudades = obtener_cines()

    except Exception as error:
        print("Error obteniendo ubicaciones:", error)
        return None

    if not ciudades:
        print("No se han encontrado ciudades.")
        return None

    # Guardar todas las ubicaciones disponibles
    registrar_ubicaciones(CADENA, ciudades)

    # Limitar a Valencia únicamente en las pruebas
    if solo_valencia:

        ciudades = [
            ciudad
            for ciudad in ciudades
            if ciudad["id"] == "valencia"
        ]

    resumen = {
        "actualizados": 0,
        "fallidos": 0,
        "omitidos": 0,
        "vacios": 0
    }

    total_cines = sum(
        len(ciudad["cines"])
        for ciudad in ciudades
    )

    print("\nCiudades a revisar:", len(ciudades))
    print("Cines a revisar:", total_cines)

    for ciudad in ciudades:

        print(f"\n--- CIUDAD: {ciudad['nombre']} ---")

        for cine in ciudad["cines"]:

            estado = actualizar_cine(cine)

            if estado == "correcto":
                resumen["actualizados"] += 1

            elif estado == "vacia":
                resumen["actualizados"] += 1
                resumen["vacios"] += 1

            elif estado == "error":
                resumen["fallidos"] += 1

            elif estado == "omitido":
                resumen["omitidos"] += 1

            if estado != "omitido":
                time.sleep(PAUSA_PETICIONES)

    print("\n" + "=" * 50)
    print("          RESUMEN ACTUALIZACIÓN")
    print("=" * 50)

    print("Actualizados:", resumen["actualizados"])
    print("Fallidos:", resumen["fallidos"])
    print("Omitidos (todavía recientes):", resumen["omitidos"])
    print("Carteleras vacías confirmadas:", resumen["vacios"])

    return resumen


# ==========================================
# EJECUTAR ACTUALIZACIÓN COMPLETA
# ==========================================

if __name__ == "__main__":
    actualizar_yelmo()
