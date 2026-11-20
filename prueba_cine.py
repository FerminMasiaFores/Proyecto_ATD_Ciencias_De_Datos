
from scrapers.yelmo import obtener_cines


def main():

    ciudades = obtener_cines()

    total_cines = sum(
        len(ciudad["cines"])
        for ciudad in ciudades
    )

    print("\n--- RESULTADOS ---")
    print("Ciudades encontradas:", len(ciudades))
    print("Cines encontrados:", total_cines)

    print("\n--- CINES DE VALENCIA ---")

    for ciudad in ciudades:

        if ciudad["id"] == "valencia":

            for cine in ciudad["cines"]:
                print(
                    f"{cine['nombre']} -> {cine['id']}"
                )


if __name__ == "__main__":
    main()
