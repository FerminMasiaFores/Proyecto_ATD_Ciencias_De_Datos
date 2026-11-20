# ==========================================
# NORMALIZADOR DE KINÉPOLIS
# ==========================================

def normalizar_pelicula_kinepolis(pelicula):

    if not isinstance(pelicula, dict):
        return None

    identificador = str(
        pelicula.get("id") or ""
    ).strip()

    titulo = str(
        pelicula.get("titulo") or ""
    ).strip()

    # Comprobar los datos fundamentales
    if not identificador or not titulo or titulo == "Sin título":
        return None

    # Normalizar duración
    duracion = pelicula.get("duracion")

    if isinstance(duracion, (int, float)) and not isinstance(duracion, bool):
        duracion = f"{int(duracion)} min" if duracion > 0 else ""

    elif isinstance(duracion, str):
        duracion = duracion.strip()

        if duracion.isdigit():
            duracion += " min"

    else:
        duracion = ""

    # Normalizar géneros
    generos = pelicula.get("generos") or []

    if not isinstance(generos, list):
        generos = [generos]

    generos = [
        genero.strip()
        for genero in generos
        if isinstance(genero, str) and genero.strip()
    ]

    # Formato común de CineData
    return {
        "cadena": "Kinépolis",
        "id_externo": identificador,
        "titulo": titulo,
        "titulo_original": "",
        "generos": generos,
        "duracion": duracion,
        "sinopsis": pelicula.get("sinopsis") or "",
        "clasificacion": pelicula.get("edad") or "",
        "fecha_estreno": str(
            pelicula.get("estreno") or ""
        )[:10]
    }


# ==========================================
# NORMALIZAR UNA LISTA DE PELÍCULAS
# ==========================================

def normalizar_peliculas_kinepolis(peliculas):

    return [
        normalizar_pelicula_kinepolis(pelicula)
        for pelicula in peliculas
    ]
