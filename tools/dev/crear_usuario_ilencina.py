import os
import psycopg2
import bcrypt
from dotenv import load_dotenv
from datetime import datetime

# Datos del usuario ilencina
USERNAME = "ilencina"
PASSWORD = "ilencina123"
NOMBRE_COMPLETO = "Iván Lencina"
EMAIL = "davidlencina7@gmail.com"
ROL = "admin"
ACTIVO = True  # Debe ser booleano para PostgreSQL
TEMA = "dark"
FECHA_CREACION = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
    hashed = bcrypt.hashpw(PASSWORD.encode('utf-8'), bcrypt.gensalt())
    hashed_str = hashed.decode('utf-8')

    # Insertar usuario ilencina
    cur.execute("""
        INSERT INTO usuarios (username, password_hash, nombre, email, rol, activo, tema_preferido, fecha_creacion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (USERNAME, hashed_str, NOMBRE_COMPLETO, EMAIL, ROL, ACTIVO, TEMA, FECHA_CREACION))
    print("Usuario ilencina creado correctamente.")

    cur.close()
    conn.close()
except Exception as e:
    print(f"Error al crear usuario ilencina: {e}")
