from scrapers.yelmo import (
    descargar_pagina,
    guardar_html,
    analizar_pagina
)


def main():
    print("========================")
    print("       CineData")
    print("========================\n")

    html = descargar_pagina()

    guardar_html(html)

    soup = analizar_pagina(html)

    print("\nHTML guardado correctamente.")
    print("Tamaño:", len(html), "caracteres")


if __name__ == "__main__":
    main()