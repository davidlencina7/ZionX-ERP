import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno desde .env.production
load_dotenv('.env.production')

# Obtener DATABASE_URL del entorno
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise RuntimeError('DATABASE_URL no está definida (ni en .env.production ni en el entorno)')

try:
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute('SELECT version();')
    print(cur.fetchone())
    cur.close()
    conn.close()
    print('Conexión exitosa a PostgreSQL.')
except Exception as e:
    print(f'Error de conexión: {e}')
