
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

EXPECTED_TABLES = [
    'productos', 'compras', 'ventas', 'movimientos_contables', 'accounts',
    # Agrega aquí otras tablas esperadas según tu dump_postgres.sql
]

def get_connection():
    # Cargar variables desde .env.production si existe
    load_dotenv('.env.production')
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise RuntimeError('DATABASE_URL no está definido en el entorno (ni en .env.production)')
    return psycopg2.connect(db_url)

def get_existing_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        """)
        return {(schema, name) for schema, name in cur.fetchall()}

def main():
    print('Verificando estructura de la base de datos...')
    conn = get_connection()
    existing = get_existing_tables(conn)
    expected = set(('public', t) for t in EXPECTED_TABLES)
    missing = expected - existing
    extra = existing - expected
    print('\nTablas esperadas que NO existen:')
    for schema, name in sorted(missing):
        print(f'- {schema}.{name}')
    print('\nTablas existentes NO esperadas (posiblemente legacy o de otros módulos):')
    for schema, name in sorted(extra):
        print(f'- {schema}.{name}')
    print('\nResumen:')
    print(f'Tablas esperadas: {len(expected)}')
    print(f'Tablas encontradas: {len(existing)}')
    print(f'Faltantes: {len(missing)}')
    print(f'Extras: {len(extra)}')
    conn.close()

if __name__ == '__main__':
    main()
