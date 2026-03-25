import os
import psycopg2
import bcrypt
from dotenv import load_dotenv

# Configura aquí tus credenciales de admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "BtLcQB5pI3XV4dR7"  # Contraseña tomada de tu archivo y selección
ADMIN_EMAIL = "admin@zionx.local"  # Puedes cambiar este correo si lo deseas

# Cargar variables de entorno
load_dotenv(".env.production")
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    print("DATABASE_URL no encontrada en .env.production")
    exit(1)

try:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # Generar hash bcrypt
    hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt())
    hashed_str = hashed.decode('utf-8')

    # Insertar usuario admin
    cur.execute("""
        INSERT INTO usuarios (username, password, email, is_admin, activo)
        VALUES (%s, %s, %s, %s, %s)
    """, (ADMIN_USERNAME, hashed_str, ADMIN_EMAIL, True, True))
    print("Usuario admin creado correctamente.")

    cur.close()
    conn.close()
except Exception as e:
    print(f"Error al crear usuario admin: {e}")
