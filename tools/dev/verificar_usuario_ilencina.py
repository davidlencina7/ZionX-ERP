import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno desde .env.production
load_dotenv('.env.production')

# Obtener DATABASE_URL del entorno
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL no está definida (ni en .env.production ni en el entorno)')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, rol, activo FROM usuarios WHERE username = %s", ('ilencina',))
    row = cur.fetchone()
    if row:
        print(f"Usuario encontrado: id={row[0]}, username={row[1]}, email={row[2]}, rol={row[3]}, activo={row[4]}")
    else:
        print("Usuario 'ilencina' NO existe en la base de datos.")
    cur.close()
    conn.close()
except Exception as e:
    print(f'Error al consultar usuario: {e}')
