import os

# Script: buscar_pg_dump.py
# Busca pg_dump.exe en la carpeta raíz y subcarpetas del proyecto

def buscar_pg_dump(directorio):
    for root, dirs, files in os.walk(directorio):
        if 'pg_dump.exe' in files:
            print(f"[ENCONTRADO] {os.path.join(root, 'pg_dump.exe')}")
            return os.path.join(root, 'pg_dump.exe')
    print("[NO ENCONTRADO] No se encontró pg_dump.exe en el árbol de carpetas.")
    return None

if __name__ == "__main__":
    raiz = os.path.abspath(os.path.dirname(__file__))
    print(f"Buscando pg_dump.exe desde: {raiz}")
    buscar_pg_dump(raiz)
