import os
from datetime import datetime

# Ruta de backups (ajustar si es necesario)
BACKUP_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'backups')
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# Nombre de archivo con timestamp
filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
filepath = os.path.join(BACKUP_DIR, filename)

# Comando para hacer backup de PostgreSQL (ajustar variables de entorno si es necesario)
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("[ERROR] No se encontró la variable de entorno DATABASE_URL")
    exit(1)

# Extraer datos de conexión
import re
m = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(\w+)", db_url)
if not m:
    print("[ERROR] DATABASE_URL no tiene el formato esperado")
    exit(1)
user, password, host, port, dbname = m.groups()

# Comando pg_dump
cmd = f"pg_dump -h {host} -p {port} -U {user} -F c -b -v -f \"{filepath}\" {dbname}"
print(f"Ejecutando backup: {cmd}")

# Ejecutar backup
os.environ['PGPASSWORD'] = password
res = os.system(cmd)
if res == 0:
    print(f"Backup exitoso: {filepath}")
else:
    print(f"[ERROR] Falló el backup (código {res})")
