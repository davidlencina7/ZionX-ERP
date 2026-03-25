import sqlite3

# Tablas adicionales a borrar si existen
tablas = [
    'movimientos_contables',
    'accounts',
    'journal_entries',
    'journal_lines',
    'plan_cuentas',
    'asientos_contables',
    'lineas_asiento',
    'operaciones',
]


for tabla in tablas:
    try:
        c.execute(f"DROP TABLE IF EXISTS {tabla}")
    except Exception as e:
        print(f"No se pudo borrar {tabla}: {e}")

print('Tablas adicionales eliminadas. Listo para restaurar dump_real.sql')
