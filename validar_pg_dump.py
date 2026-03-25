import shutil
import sys
import os

# Script: validar_pg_dump.py
# Uso: python validar_pg_dump.py

def main():
    print("[VALIDACIÓN] Verificando presencia de 'pg_dump' en el PATH...")
    pg_dump_path = shutil.which('pg_dump')
    if pg_dump_path:
        print(f"[OK] pg_dump encontrado en: {pg_dump_path}")
        sys.exit(0)
    else:
        print("[ERROR] No se encontró 'pg_dump' en el PATH del sistema.")
        print("Agrega la carpeta 'bin' de tu instalación de PostgreSQL al PATH antes de continuar.")
        if os.name == 'nt':
            print("Ejemplo de ruta: C:/Program Files/PostgreSQL/15/bin")
        sys.exit(1)

if __name__ == "__main__":
    main()
