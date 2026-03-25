import os
from dotenv import load_dotenv
import psycopg2

# Cargar variables de entorno desde .env o .env.production
env_files = ['.env', '.env.production']
for env_file in env_files:
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)

url = os.environ.get('DATABASE_URL')
print('DATABASE_URL:', url)
if not url:
    print('No se encontró la variable DATABASE_URL')
    exit(1)

try:
    conn = psycopg2.connect(url)
    print('Conexión exitosa a la base de datos')
    conn.close()
except Exception as e:
    print('Error de conexión:', e)
    exit(2)
