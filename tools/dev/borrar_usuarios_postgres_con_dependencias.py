import os
import psycopg2
from dotenv import load_dotenv

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

    # Eliminar primero los registros dependientes en activos
    cur.execute("DELETE FROM activos;")
    print("Registros de 'activos' eliminados.")

    # Si hay otras tablas dependientes, agregar aquí más DELETE
    # cur.execute("DELETE FROM otra_tabla_dependiente;")

    # Ahora eliminar los usuarios
    cur.execute("DELETE FROM usuarios;")
    print("Usuarios eliminados correctamente.")

    cur.close()
    conn.close()
except Exception as e:
    print(f"Error al eliminar usuarios y dependencias: {e}")
