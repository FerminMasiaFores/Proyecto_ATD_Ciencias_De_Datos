
import socket
import json

from almacenamiento.database import conectar, crear_tablas
from api.tmdb import buscar_pelicula_tmdb

import time
from threading import Thread

from actualizar_datos import actualizar_yelmo
from actualizar_abc import actualizar_abc
from actualizar_kinepolis import actualizar_kinepolis

HOST = "127.0.0.1"
PORT = 5000


# ==========================================
# PROCESAR PETICIONES
# ==========================================

def procesar_peticion(peticion):

    accion = peticion.get("accion")

    # ======================================
    # LISTAR CADENAS
    # ======================================

    if accion == "listar_cadenas":

        conexion = conectar()

        try:
            filas = conexion.execute("""
                SELECT DISTINCT ciudad.cadena
                FROM ciudades ciudad
                JOIN cine_ciudad relacion
                    ON ciudad.cadena = relacion.cadena
                    AND ciudad.id_externo = relacion.id_ciudad
                ORDER BY ciudad.cadena COLLATE NOCASE
            """).fetchall()

            cadenas = [fila[0] for fila in filas]

            return {"ok": True, "datos": cadenas}

        finally:
            conexion.close()

    # ======================================
    # LISTAR CIUDADES DE UNA CADENA
    # ======================================

    elif accion == "listar_ciudades":

        cadena = peticion.get("cadena")

        if not cadena:
            return {
                "ok": False,
                "error": "Falta indicar la cadena"
            }

        conexion = conectar()

        try:
            filas = conexion.execute("""
                SELECT DISTINCT
                    ciudad.id_externo,
                    ciudad.nombre

                FROM ciudades ciudad

                JOIN cine_ciudad relacion
                    ON ciudad.cadena = relacion.cadena
                    AND ciudad.id_externo = relacion.id_ciudad

                WHERE ciudad.cadena = ?

                ORDER BY ciudad.nombre COLLATE NOCASE
            """, (cadena,)).fetchall()

            ciudades = [
                {"id": fila[0], "nombre": fila[1]}
                for fila in filas
            ]

            return {"ok": True, "datos": ciudades}

        finally:
            conexion.close()

    # ======================================
    # LISTAR CINES DE UNA CIUDAD
    # ======================================

    elif accion == "listar_cines":

        cadena = peticion.get("cadena")
        id_ciudad = peticion.get("id_ciudad")

        if not cadena or not id_ciudad:
            return {
                "ok": False,
                "error": "Falta cadena o id_ciudad"
            }

        conexion = conectar()

        try:
            filas = conexion.execute("""
                SELECT
                    cine.id_externo,
                    cine.nombre

                FROM cines cine

                JOIN cine_ciudad relacion
                    ON cine.cadena = relacion.cadena
                    AND cine.id_externo = relacion.id_cine

                WHERE relacion.cadena = ?
                    AND relacion.id_ciudad = ?

                ORDER BY cine.nombre COLLATE NOCASE
            """, (cadena, id_ciudad)).fetchall()

            cines = [
                {
                    "id": fila[0],
                    "nombre": fila[1],
                    "cadena": cadena
                }
                for fila in filas
            ]

            return {"ok": True, "datos": cines}

        finally:
            conexion.close()

    # ======================================
    # LISTAR PELÍCULAS DE UN CINE
    # ======================================

    elif accion == "listar_peliculas":

        cadena = peticion.get("cadena")
        id_cine = peticion.get("id_cine")

        if not cadena or not id_cine:
            return {
                "ok": False,
                "error": "Falta cadena o id_cine"
            }

        conexion = conectar()

        try:
            filas = conexion.execute("""
                SELECT
                    p.id_externo,
                    p.titulo

                FROM peliculas p

                JOIN cine_pelicula cp
                    ON p.cadena = cp.cadena
                    AND p.id_externo = cp.id_pelicula

                WHERE cp.cadena = ?
                    AND cp.id_cine = ?

                ORDER BY p.titulo COLLATE NOCASE
            """, (cadena, id_cine)).fetchall()

            peliculas = [
                {
                    "id": fila[0],
                    "titulo": fila[1]
                }
                for fila in filas
            ]

            return {"ok": True, "datos": peliculas}

        finally:
            conexion.close()

    # ======================================
    # CONSULTAR FICHA DE PELÍCULA
    # ======================================

    elif accion == "detalle_pelicula":

        cadena = peticion.get("cadena")
        id_cine = peticion.get("id_cine")
        id_pelicula = peticion.get("id_pelicula")

        if not cadena or not id_cine or not id_pelicula:
            return {
                "ok": False,
                "error": "Faltan datos de la petición"
            }

        conexion = conectar()

        try:
            fila = conexion.execute("""
                SELECT
                    p.titulo,
                    p.titulo_original,
                    p.generos,
                    p.duracion,
                    p.sinopsis,
                    p.clasificacion,
                    p.fecha_estreno

                FROM peliculas p

                JOIN cine_pelicula cp
                    ON p.cadena = cp.cadena
                    AND p.id_externo = cp.id_pelicula

                WHERE cp.cadena = ?
                    AND cp.id_cine = ?
                    AND cp.id_pelicula = ?
            """, (
                cadena,
                id_cine,
                id_pelicula
            )).fetchone()

        finally:
            conexion.close()

        if fila is None:
            return {
                "ok": False,
                "error": "Película no encontrada"
            }

        pelicula = {
            "titulo": fila[0],
            "titulo_original": fila[1],
            "generos": json.loads(fila[2]) if fila[2] else [],
            "duracion": fila[3],
            "sinopsis": fila[4],
            "clasificacion": fila[5],
            "fecha_estreno": fila[6],
            "tmdb": None
        }

        # Consultar TMDb
        try:
            datos_tmdb = buscar_pelicula_tmdb(
                pelicula["titulo"],
                pelicula["titulo_original"] or "",
                pelicula["fecha_estreno"] or ""
            )

            if datos_tmdb:
                pelicula["tmdb"] = {
                    "valoracion": datos_tmdb.get("vote_average"),
                    "votos": datos_tmdb.get("vote_count", 0),
                    "id": datos_tmdb.get("id")
                }

        except Exception as error:
            print("Error consultando TMDb:", error)

        return {
            "ok": True,
            "datos": pelicula
        }

    # ======================================
    # ACCIÓN DESCONOCIDA
    # ======================================

    return {
        "ok": False,
        "error": "Acción desconocida"
    }



# ==========================================
# ACTUALIZACIONES AUTOMÁTICAS DE CINEDATA
# ==========================================

def ciclo_actualizaciones():

    while True:

        print("\n" + "=" * 50)
        print("   ACTUALIZACIONES AUTOMÁTICAS CINEDATA")
        print("=" * 50)

        # ==================================
        # CADENAS CON ACTUALIZACIÓN AUTOMÁTICA
        # ==================================

        actualizadores = [
            ("Yelmo", actualizar_yelmo),
            ("Kinépolis", actualizar_kinepolis),
            ("ABC", actualizar_abc)
        ]


        # ==================================
        # ACTUALIZAR CADA CADENA
        # ==================================

        for nombre_cadena, funcion_actualizar in actualizadores:

            print("\n" + "=" * 50)
            print(f"      COMPROBANDO {nombre_cadena.upper()}")
            print("=" * 50)

            try:

                # Ejecutar el actualizador correspondiente
                resultado = funcion_actualizar()

                if resultado is None:

                    print(
                        f"\nNo se ha podido completar "
                        f"la comprobación de {nombre_cadena}."
                    )

                    print(
                        "Se conservarán los últimos "
                        "datos disponibles en SQLite."
                    )

                    continue

                # ==================================
                # MOSTRAR RESUMEN
                # ==================================

                print("\n--- RESULTADO DE LA CADENA ---")

                print("Cadena:", nombre_cadena)

                print(
                    "Cines actualizados:",
                    resultado.get("actualizados", 0)
                )

                print(
                    "Cines fallidos:",
                    resultado.get("fallidos", 0)
                )

                print(
                    "Cines omitidos:",
                    resultado.get("omitidos", 0)
                )

                # Yelmo también distingue
                # carteleras vacías confirmadas
                if "vacios" in resultado:

                    print(
                        "Carteleras vacías:",
                        resultado["vacios"]
                    )

            except Exception as error:

                print(
                    f"\nERROR actualizando "
                    f"{nombre_cadena}: {error}"
                )

                print(
                    "Se conservan los datos anteriores."
                )

                # Un error en una cadena no impide
                # actualizar las demás
                continue

        # ==================================
        # FINAL DEL CICLO
        # ==================================

        print("\n" + "=" * 50)
        print("    COMPROBACIÓN GENERAL FINALIZADA")
        print("=" * 50)

        print(
            "\nPróxima comprobación en 30 minutos."
        )

        # Esperar antes de comprobar de nuevo
        time.sleep(30 * 60)




# ==========================================
# INICIAR SERVIDOR TCP
# ==========================================

def iniciar_servidor():

    crear_tablas()

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    ) as servidor:

        servidor.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        servidor.bind((HOST, PORT))
        servidor.listen()

        print("=" * 40)
        print("          SERVIDOR CINEDATA")
        print("=" * 40)

        print(f"Escuchando en {HOST}:{PORT}")

        # Actualizar en un hilo independiente,
        # sin bloquear las conexiones TCP.

        # Ejecutar actualizaciones en segundo plano
        # mientras el servidor atiende clientes.

        hilo_actualizacion = Thread(
            target=ciclo_actualizaciones,
            daemon=True
        )

        hilo_actualizacion.start()


        # Continuar atendiendo clientes
        while True:


            conexion_cliente, direccion = servidor.accept()

            with conexion_cliente:

                conexion_cliente.settimeout(30)

                try:
                    with conexion_cliente.makefile(
                        "r",
                        encoding="utf-8"
                    ) as entrada:
                        mensaje = entrada.readline()

                    if not mensaje:
                        continue

                    peticion = json.loads(mensaje)

                    if not isinstance(peticion, dict):
                        raise ValueError("Petición no válida")

                    print("Petición recibida:", peticion)

                    respuesta = procesar_peticion(peticion)

                except ValueError as error:
                    respuesta = {
                        "ok": False,
                        "error": str(error)
                    }

                except Exception as error:
                    print("Error del servidor:", error)
                    respuesta = {
                        "ok": False,
                        "error": "Error interno del servidor"
                    }

                mensaje_respuesta = (
                    json.dumps(respuesta, ensure_ascii=False)
                    + "\n"
                )

                try:
                    conexion_cliente.sendall(
                        mensaje_respuesta.encode("utf-8")
                    )
                except OSError as error:
                    print("Error enviando respuesta:", error)


if __name__ == "__main__":

    try:
        iniciar_servidor()

    except KeyboardInterrupt:
        print("\nServidor detenido.")
