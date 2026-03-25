import sqlite3

# Tablas a borrar (orden para evitar conflictos de FK)
tablas = [
    'ventas',
    'compras',
    'productos',
    'usuarios',
    'gastos',
    'activos',
    'inventory_movements',
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

print('Tablas eliminadas. Listo para restaurar dump_real.sql')
# Eliminado: solo PostgreSQL
