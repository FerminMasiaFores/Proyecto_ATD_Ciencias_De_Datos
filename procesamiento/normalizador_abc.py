
import hashlib
import re
import unicodedata

from datetime import datetime


# ==========================================
# GENERAR IDENTIFICADOR DE PELÍCULA
# ==========================================

def generar_id(titulo):

    texto = unicodedata.normalize(
        "NFKD",
        titulo.casefold()
    )

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = re.sub(r"\s+", " ", texto).strip()

    identificador = hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()[:20]

    return f"abc-{identificador}"


# ==========================================
# NORMALIZAR GÉNEROS
# ==========================================

def normalizar_generos(valor):

    if isinstance(valor, list):
        valores = valor

    elif isinstance(valor, str):
        valores = re.split(r"[,;/|]", valor)

    else:
        valores = []

    return [
        genero.strip()
        for genero in valores
        if isinstance(genero, str) and genero.strip()
    ]


# ==========================================
# NORMALIZAR DURACIÓN
# ==========================================

def normalizar_duracion(valor):

    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return f"{int(valor)} min" if valor > 0 else ""

    if isinstance(valor, str):

        valor = valor.strip()

        if valor.isdigit():
            return f"{valor} min"

        return valor

    return ""


# ==========================================
# NORMALIZAR FECHA DE ESTRENO
# ==========================================

def normalizar_fecha(valor):

    if not valor:
        return ""

    texto = str(valor).strip()

    formatos = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y"
    ]

    for formato in formatos:
        try:
            fecha = datetime.strptime(texto, formato)
            return fecha.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return ""


# ==========================================
# NORMALIZAR UNA PELÍCULA ABC
# ==========================================

def normalizar_pelicula_abc(pelicula):

    if not isinstance(pelicula, dict):
        raise ValueError("Película ABC no válida.")

    titulo = str(
        pelicula.get("name") or ""
    ).strip()

    if not titulo:
        raise ValueError(
            "La película no tiene título."
        )

    titulo_original = str(
        pelicula.get("originalName") or ""
    ).strip()

    return {
        "cadena": "ABC",
        "id_externo": generar_id(titulo),
        "titulo": titulo,
        "titulo_original": titulo_original,
        "generos": normalizar_generos(
            pelicula.get("genre")
        ),
        "duracion": normalizar_duracion(
            pelicula.get("length")
        ),
        "sinopsis": pelicula.get("synopsis") or "",
        "clasificacion": str(
            pelicula.get("rating") or ""
        ).strip(),
        "fecha_estreno": normalizar_fecha(
            pelicula.get("releaseDate")
        )
    }


# ==========================================
# NORMALIZAR LISTA DE PELÍCULAS ABC
# ==========================================

def normalizar_peliculas_abc(peliculas):

    resultado = {}

    for pelicula in peliculas:

        normalizada = normalizar_pelicula_abc(
            pelicula
        )

        identificador = normalizada["id_externo"]

        # Evitar duplicados de una misma película
        resultado[identificador] = normalizada

    return list(resultado.values())
