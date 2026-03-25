import os
import psycopg2
import dotenv

dotenv.load_dotenv()
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    dotenv.load_dotenv('.env.production')
    db_url = os.environ.get('DATABASE_URL')

conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute('SELECT rolsuper FROM pg_roles WHERE rolname = current_user;')
superuser = cur.fetchone()[0]
print(f"¿Usuario actual es superusuario?: {'SÍ' if superuser else 'NO'}")
cur.close()
conn.close()
