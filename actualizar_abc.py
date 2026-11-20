
import time

from scrapers.abc import (
    CINES_ABC,
    obtener_peliculas
)

from procesamiento.normalizador_abc import (
    normalizar_peliculas_abc
)

from integracion.abc import obtener_ubicaciones_abc

from integracion.cadenas import (
    registrar_ubicaciones,
    registrar_cartelera
)

from almacenamiento.database import (
    conectar,
    crear_tablas
)


# ==========================================
# CONFIGURACIÓN
# ==========================================

CADENA = "ABC"

HORAS_ACTUALIZACION = 24
MINUTOS_REINTENTO = 30
PAUSA_PETICIONES = 1


# ==========================================
# CREAR TABLA DE CONTROL
# ==========================================

def crear_control_abc():

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
# CONSULTAR ÚLTIMA ACTUALIZACIÓN
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
        """, (
            CADENA,
            id_cine
        )).fetchone()

    finally:
        conexion.close()


# ==========================================
# COMPROBAR SI NECESITA ACTUALIZACIÓN
# ==========================================

def necesita_actualizacion(id_cine):

    registro = consultar_estado(id_cine)

    if registro is None:
        return True

    ultimo_intento, ultimo_exito, estado = registro

    ahora = int(time.time())

    # Si hubo un error, reintentar a los 30 minutos
    if estado == "error":

        if ultimo_intento is not None:
            segundos = MINUTOS_REINTENTO * 60

            if ahora - ultimo_intento < segundos:
                return False

        return True

    # Si la última actualización correcta es reciente
    if ultimo_exito is not None:

        segundos = HORAS_ACTUALIZACION * 3600

        if ahora - ultimo_exito < segundos:
            return False

    return True


# ==========================================
# GUARDAR ESTADO DE UN CINE
# ==========================================

def registrar_estado(id_cine, estado, detalle=""):

    ahora = int(time.time())

    ultimo_exito = (
        ahora
        if estado == "correcto"
        else None
    )

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

                    ultimo_intento =
                        excluded.ultimo_intento,

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
# ACTUALIZAR UN CINE ABC
# ==========================================

def actualizar_cine_abc(nombre_cine, datos_cine):

    id_cine = datos_cine["subdominio"]

    print("\n" + "-" * 45)
    print("Cine:", nombre_cine)

    # Comprobar fecha de actualización
    if not necesita_actualizacion(id_cine):

        print("Actualización no necesaria todavía.")
        return "omitido"

    try:

        # 1. Descargar películas desde ABC
        originales = obtener_peliculas(nombre_cine)

        if not isinstance(originales, list):
            raise ValueError(
                "Respuesta de cartelera no válida."
            )

        # No borrar una cartelera anterior
        # por una respuesta vacía no confirmada
        if not originales:
            raise ValueError(
                "La fuente no ha devuelto películas."
            )

        print(
            "Películas descargadas:",
            len(originales)
        )

        # 2. Normalizar
        normalizadas = normalizar_peliculas_abc(
            originales
        )

        if not normalizadas:
            raise ValueError(
                "No se han normalizado películas."
            )

        identificadores = [
            pelicula["id_externo"]
            for pelicula in normalizadas
        ]

        if len(identificadores) != len(set(identificadores)):
            raise ValueError(
                "Existen identificadores duplicados."
            )

        # 3. Guardar en SQLite
        cantidad = registrar_cartelera(
            CADENA,
            id_cine,
            nombre_cine,
            normalizadas
        )

        # 4. Registrar actualización correcta
        registrar_estado(
            id_cine,
            "correcto",
            f"{cantidad} películas guardadas."
        )

        print("Películas guardadas:", cantidad)

        return "correcto"

    except Exception as error:

        print("ERROR:", error)
        print(
            "Se conservan los datos anteriores."
        )

        registrar_estado(
            id_cine,
            "error",
            str(error)
        )

        return "error"


# ==========================================
# ACTUALIZACIÓN GENERAL DE ABC
# ==========================================

def actualizar_abc():

    print("\n" + "=" * 50)
    print("       ACTUALIZACIÓN CINES ABC")
    print("=" * 50)

    crear_tablas()
    crear_control_abc()

    # Registrar las ubicaciones de ABC
    ciudades = obtener_ubicaciones_abc()

    total_ciudades, total_cines = registrar_ubicaciones(
        CADENA,
        ciudades
    )

    print("\nCiudades ABC:", total_ciudades)
    print("Cines ABC:", total_cines)

    resumen = {
        "actualizados": 0,
        "fallidos": 0,
        "omitidos": 0
    }

    # Procesar los cinco cines
    for nombre_cine, datos_cine in CINES_ABC.items():

        estado = actualizar_cine_abc(
            nombre_cine,
            datos_cine
        )

        if estado == "correcto":
            resumen["actualizados"] += 1

        elif estado == "error":
            resumen["fallidos"] += 1

        elif estado == "omitido":
            resumen["omitidos"] += 1

        if estado != "omitido":
            time.sleep(PAUSA_PETICIONES)

    print("\n" + "=" * 50)
    print("       RESUMEN ACTUALIZACIÓN ABC")
    print("=" * 50)

    print("Actualizados:", resumen["actualizados"])
    print("Fallidos:", resumen["fallidos"])
    print("Omitidos:", resumen["omitidos"])

    return resumen


# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    actualizar_abc()
