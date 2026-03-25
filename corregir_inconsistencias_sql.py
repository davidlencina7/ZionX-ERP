"""
Script de corrección de inconsistencias de SQL entre SQLite y PostgreSQL en ZionX ERP.
- Reemplaza el uso de PRAGMA table_info por una consulta compatible con ambos motores.
- Aplica la corrección en backend/services/compras_service.py.
- Genera un resumen de los cambios realizados.

Uso:
    python corregir_inconsistencias_sql.py
"""
"""
Script de corrección de inconsistencias de SQL entre SQLite y PostgreSQL en ZionX ERP.
 Reemplaza el uso de PRAGMA table_info por una consulta compatible con ambos motores.
 Aplica la corrección en backend/services/compras_service.py.
 Genera un resumen de los cambios realizados.

Uso:
    python corregir_inconsistencias_sql.py
"""
import os
import re

RUTA = os.path.join('backend', 'services', 'compras_service.py')

# Patrón para encontrar cursor.execute("PRAGMA table_info(compras)")
PATRON_PRAGMA = re.compile(r'cursor\.execute\(["\']PRAGMA table_info\(compras\)["\']\)')

# Consulta para obtener columnas en PostgreSQL
QUERY_PG = "SELECT column_name FROM information_schema.columns WHERE table_name = 'compras';"

# Lee el archivo original
def leer_archivo(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()

def escribir_archivo(ruta, contenido):
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(contenido)

def corregir_pragma_por_postgres(contenido):
    cambios = 0
    def reemplazo(match):
        nonlocal cambios
        cambios += 1
        return (
            "try:\n"
            "    cursor.execute(\"%s\")\n"
            "    columnas = [col[0] for col in cursor.fetchall()]\n"
            "except Exception:\n"
            "    cursor.execute(\"PRAGMA table_info(compras)\")\n"
            "    columnas = [col[1] for col in cursor.fetchall()]\n" % QUERY_PG
        )
    nuevo = PATRON_PRAGMA.sub(reemplazo, contenido)
    return nuevo, cambios

def main():
    print(f"Corrigiendo inconsistencias en: {RUTA}")
    original = leer_archivo(RUTA)
    corregido, cambios = corregir_pragma_por_postgres(original)
    if cambios == 0:
        print("No se encontraron usos de PRAGMA table_info(compras) para corregir.")
        return
    escribir_archivo(RUTA, corregido)
    print(f"Se corrigieron {cambios} ocurrencias de PRAGMA table_info(compras).\n")
    print("¡Corrección completada! Ahora puedes volver a ejecutar tus scripts de diagnóstico.")

if __name__ == "__main__":
    main()
