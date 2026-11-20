
import time

from scrapers import kinepolis as scraper

from integracion.kinepolis import (
    CIUDAD_POR_CINE,
    agrupar_cines_por_ciudad
)

from procesamiento.normalizador_kinepolis import (
    normalizar_peliculas_kinepolis
)

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

CADENA = "Kinépolis"

HORAS_ACTUALIZACION = 24
MINUTOS_REINTENTO = 30


# ==========================================
# CREAR TABLA DE CONTROL
# ==========================================

def crear_control_kinepolis():

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
# CONSULTAR ESTADOS GUARDADOS
# ==========================================

def obtener_estados():

    conexion = conectar()

    try:
        filas = conexion.execute("""
            SELECT
                id_cine,
                ultimo_intento,
                ultimo_exito,
                estado

            FROM control_actualizaciones_cine

            WHERE cadena = ?
        """, (CADENA,)).fetchall()

        return {
            fila[0]: {
                "ultimo_intento": fila[1],
                "ultimo_exito": fila[2],
                "estado": fila[3]
            }
            for fila in filas
        }

    finally:
        conexion.close()


# ==========================================
# COMPROBAR SI NECESITA ACTUALIZACIÓN
# ==========================================

def necesita_actualizacion(registro, ahora):

    if registro is None:
        return True

    ultimo_intento = registro["ultimo_intento"]
    ultimo_exito = registro["ultimo_exito"]
    estado = registro["estado"]

    # Los errores se reintentan después de 30 minutos.
    if estado == "error":

        if ultimo_intento is None:
            return True

        return (
            ahora - ultimo_intento
            >= MINUTOS_REINTENTO * 60
        )

    # Una actualización correcta dura 24 horas.
    if ultimo_exito is None:
        return True

    return (
        ahora - ultimo_exito
        >= HORAS_ACTUALIZACION * 3600
    )


# ==========================================
# REGISTRAR ESTADO DE UN CINE
# ==========================================

def registrar_estado(id_cine, estado, detalle=""):

    ahora = int(time.time())

    ultimo_exito = (
        ahora
        if estado in ("correcto", "vacia")
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
# ACTUALIZAR KINÉPOLIS
# ==========================================

def actualizar_kinepolis():

    print("\n" + "=" * 50)
    print("       ACTUALIZACIÓN KINÉPOLIS")
    print("=" * 50)

    crear_tablas()
    crear_control_kinepolis()

    estados = obtener_estados()
    ahora = int(time.time())

    # Utilizar los identificadores ya configurados
    # en nuestro módulo de integración.
    identificadores = set(CIUDAD_POR_CINE)

    pendientes = {
        id_cine
        for id_cine in identificadores
        if necesita_actualizacion(
            estados.get(id_cine),
            ahora
        )
    }

    resumen = {
        "actualizados": 0,
        "fallidos": 0,
        "omitidos": len(identificadores) - len(pendientes),
        "vacios": 0
    }

    print("\nCines configurados:", len(identificadores))
    print("Cines pendientes:", len(pendientes))
    print("Cines recientes:", resumen["omitidos"])

    # ======================================
    # NO DESCARGAR SI TODO ESTÁ ACTUALIZADO
    # ======================================

    if not pendientes:

        print(
            "\nTodas las carteleras están recientes."
        )

        print(
            "No es necesario consultar la web."
        )

        return resumen

    # ======================================
    # UNA ÚNICA DESCARGA PARA TODOS LOS CINES
    # ======================================

    try:

        print("\nDescargando información nueva...")

        # Descarga forzada.
        # No utiliza el JSON local como respaldo.
        datos = scraper.actualizar_cartelera()

        # La descarga ya ha sido validada
        # por el propio scraper.
        cines = scraper.obtener_cines()

        if not cines:
            raise ValueError(
                "No se han encontrado cines."
            )

        ids_descargados = {
            cine["id"]
            for cine in cines
        }

        # Detectar posibles cines nuevos.
        desconocidos = (
            ids_descargados - identificadores
        )

        if desconocidos:
            raise ValueError(
                "Hay cines sin ciudad configurada: "
                + ", ".join(sorted(desconocidos))
            )

        # Guardar ubicaciones actualizadas.
        ciudades = agrupar_cines_por_ciudad(cines)

        registrar_ubicaciones(
            CADENA,
            ciudades
        )

        print("\nCines recibidos:", len(cines))
        print("Ciudades:", len(ciudades))

    except Exception as error:

        print("\nERROR descargando Kinépolis:", error)

        print(
            "Se conservarán las carteleras "
            "anteriores en SQLite."
        )

        # Registrar el fallo de cada cine pendiente.
        for id_cine in pendientes:

            registrar_estado(
                id_cine,
                "error",
                str(error)
            )

        resumen["fallidos"] = len(pendientes)

        return resumen

    # ======================================
    # GUARDAR LAS CARTELERAS PENDIENTES
    # ======================================

    procesados = set()

    for cine in cines:

        id_cine = cine["id"]
        nombre_cine = cine["nombre"]

        if id_cine not in pendientes:
            continue

        procesados.add(id_cine)

        print("\n" + "-" * 45)
        print("Cine:", nombre_cine)

        try:

            # Se utiliza la cartelera recién descargada
            # que el scraper conserva en memoria.
            originales = scraper.obtener_peliculas(
                id_cine
            )

            if not isinstance(originales, list):
                raise ValueError(
                    "Lista de películas no válida."
                )

            # Normalizar para SQLite.
            normalizadas = normalizar_peliculas_kinepolis(
                originales
            )

            if any(
                pelicula is None
                for pelicula in normalizadas
            ):
                raise ValueError(
                    "Normalización incompleta."
                )

            # Comprobar identificadores duplicados.
            ids_peliculas = [
                pelicula["id_externo"]
                for pelicula in normalizadas
            ]

            if len(ids_peliculas) != len(set(ids_peliculas)):
                raise ValueError(
                    "Identificadores de películas duplicados."
                )

            # Guardar la cartelera.
            cantidad = registrar_cartelera(
                CADENA,
                id_cine,
                nombre_cine,
                normalizadas
            )

            if cantidad == 0:

                # La descarga web fue correcta y no
                # contiene películas con sesiones futuras
                # para este cine.
                registrar_estado(
                    id_cine,
                    "vacia",
                    "Sin películas con sesiones futuras."
                )

                resumen["vacios"] += 1

                print("Cartelera vacía confirmada.")

            else:

                registrar_estado(
                    id_cine,
                    "correcto",
                    f"{cantidad} películas guardadas."
                )

                print("Películas guardadas:", cantidad)

            resumen["actualizados"] += 1

        except Exception as error:

            print("ERROR:", error)

            registrar_estado(
                id_cine,
                "error",
                str(error)
            )

            resumen["fallidos"] += 1

            print(
                "Se conserva la cartelera anterior "
                "de este cine."
            )

    # Cines configurados que no aparecieron
    # en los datos descargados.
    faltantes = pendientes - procesados

    for id_cine in faltantes:

        print(
            "\nCine no encontrado en la descarga:",
            id_cine
        )

        registrar_estado(
            id_cine,
            "error",
            "Cine ausente en la descarga."
        )

        resumen["fallidos"] += 1

    # ======================================
    # RESUMEN FINAL
    # ======================================

    print("\n" + "=" * 50)
    print("       RESUMEN ACTUALIZACIÓN KINÉPOLIS")
    print("=" * 50)

    print("Cines actualizados:", resumen["actualizados"])
    print("Cines fallidos:", resumen["fallidos"])
    print("Cines omitidos:", resumen["omitidos"])
    print("Carteleras vacías:", resumen["vacios"])

    return resumen


# ==========================================
# EJECUCIÓN INDEPENDIENTE
# ==========================================

if __name__ == "__main__":
    actualizar_kinepolis()
