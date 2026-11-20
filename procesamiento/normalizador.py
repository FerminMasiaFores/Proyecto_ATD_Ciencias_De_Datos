
# ==========================================
# NORMALIZACIÓN DE PELÍCULAS
# ==========================================


def normalizar_pelicula_yelmo(pelicula):
    """
    Convierte una película de Yelmo
    al formato común de CineData.
    """

    id_pelicula = pelicula.get("id") or ""
    titulo = pelicula.get("name") or ""

    # Si falta la información básica,
    # no podemos identificar la película.
    if not id_pelicula or not titulo:
        return None

    return {
        "cadena": "Yelmo",
        "id_externo": id_pelicula,
        "titulo": titulo,
        "titulo_original": pelicula.get("originalName") or "",
        "generos": pelicula.get("genre") or [],
        "duracion": pelicula.get("length") or "",
        "sinopsis": pelicula.get("synopsis") or "",
        "clasificacion": pelicula.get("rating") or "",
        "fecha_estreno": (
            pelicula.get("releaseDate") or ""
        )[:10]
    }


def normalizar_peliculas_yelmo(peliculas):
    """
    Normaliza una lista completa
    de películas de Yelmo.
    """

    resultado = []

    for pelicula in peliculas:

        normalizada = normalizar_pelicula_yelmo(
            pelicula
        )

        if normalizada is not None:
            resultado.append(normalizada)

    return resultado