import os
import psycopg2

# Cargar variables de entorno desde .env.production si es necesario
from dotenv import load_dotenv
load_dotenv('.env.production')

url = os.environ.get('DATABASE_URL')
if not url:
    print('DATABASE_URL no está definida')
    exit(1)

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios")
    conn.commit()
    print('Todos los usuarios han sido eliminados de la tabla usuarios.')
    cur.close()
    conn.close()
except Exception as e:
    print(f'Error al conectar o eliminar usuarios: {e}')
