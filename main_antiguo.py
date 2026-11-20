
from menus.menu_yelmo import main as iniciar_yelmo
from menus.menu_kinepolis import main as iniciar_kinepolis
from menus.menu_abc import main as iniciar_abc


# ==========================================
# CONFIGURACIÓN DE CADENAS
# ==========================================

CADENAS = {
    "1": ("Yelmo", iniciar_yelmo),
    "2": ("Kinépolis", iniciar_kinepolis),
    "3": ("ABC", iniciar_abc)
}


# ==========================================
# MOSTRAR MENÚ PRINCIPAL
# ==========================================

def mostrar_menu():

    print("\n" + "=" * 50)
    print("                    CINEDATA")
    print("=" * 50)

    print("\n--- SELECCIONAR CADENA DE CINES ---\n")

    for numero, (nombre, _) in CADENAS.items():
        print(f"{numero}. {nombre}")

    print("\n0. Salir")


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

def main():

    while True:

        mostrar_menu()

        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "0":
            print("\n¡Hasta pronto!")
            break

        if opcion not in CADENAS:
            print("\nOpción no válida. Inténtalo de nuevo.")
            continue

        nombre, iniciar_cadena = CADENAS[opcion]

        print(f"\nHas seleccionado: {nombre}")

        # Ejecutar el módulo de la cadena elegida
        iniciar_cadena()


# ==========================================
# INICIAR CINEDATA
# ==========================================

if __name__ == "__main__":
    main()
