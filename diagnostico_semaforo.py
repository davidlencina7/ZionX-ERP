import os
import sys
import shutil
import subprocess
import importlib.util
from colorama import Fore, Style, init
from datetime import datetime


init(autoreset=True)


TOTAL_TESTS = 6
success = 0
fail = 0
warnings = 0
errores = 0
reporte = []


def log_reporte(msg):
    print(msg)
    reporte.append(msg)

print("\n==============================")
def advertencia_python_global():
    # Detecta si el intérprete activo NO es el de .venv aunque el prompt lo indique
    venv_path = os.path.abspath('.venv')
    exe = os.path.abspath(sys.executable)
    if venv_path in exe:
        return False
    # Si existe .venv pero el ejecutable no está dentro, advertir
    if os.path.isdir('.venv'):
        log_reporte(Fore.YELLOW + "\nADVERTENCIA: El intérprete Python activo NO es el de .venv.\n" \
            "El diagnóstico será inválido.\n" \
            f"Intérprete actual: {exe}\n" \
            f"Intérprete recomendado: {os.path.join(venv_path, 'Scripts', 'python.exe')}\n" \
            "Ejecuta el script así para diagnóstico realista:\n" \
            f"    .venv\\Scripts\\python.exe {os.path.basename(__file__)}\n")
        return True
    return False

if advertencia_python_global():
    # Si el intérprete no es el de .venv, abortar diagnóstico
    sys.exit(1)
log_reporte(" DIAGNÓSTICO ZIONX ERP - SEMÁFORO ")
log_reporte("==============================\n")

# 1. Validación de entorno virtual

print("[1/6] Entorno virtual (.venv): ", end="")
def detect_venv():
    # Debug print para ver valores
    # print(f"\n[DEBUG] VIRTUAL_ENV={os.environ.get('VIRTUAL_ENV')}")
    # print(f"[DEBUG] sys.prefix={sys.prefix}")
    # print(f"[DEBUG] sys.executable={sys.executable}")
    # print(f"[DEBUG] os.path.isdir(.venv)={os.path.isdir('.venv')}")
    # print(f"[DEBUG] os.path.basename(sys.prefix)={os.path.basename(sys.prefix)}")
    # 1. VIRTUAL_ENV variable
    if os.environ.get("VIRTUAL_ENV"):
        print("[DEBUG] detect_venv: VIRTUAL_ENV detectado")
        return True
    # 2. sys.prefix contiene .venv
    if ".venv" in sys.prefix:
        print("[DEBUG] detect_venv: .venv en sys.prefix")
        return True
    # 3. sys.executable dentro de .venv
    if ".venv" in sys.executable:
        print("[DEBUG] detect_venv: .venv en sys.executable")
        return True
    # 4. VS Code: settings de entorno
    if os.path.isdir(".venv") and os.path.basename(sys.prefix).lower() == ".venv":
        print("[DEBUG] detect_venv: sys.prefix termina en .venv y existe .venv")
        return True
    print("[DEBUG] detect_venv: NO DETECTADO")
    return False

if detect_venv():
    log_reporte(Fore.GREEN + "OK")
    success += 1
else:
    log_reporte(Fore.RED + "NO DETECTADO")
    fail += 1
    errores += 1


# 2. Validación de .env y .env.production
print("[2/6] Archivos de entorno (.env, .env.production): ", end="")
if os.path.isfile(".env") and os.path.isfile(".env.production"):
    log_reporte(Fore.GREEN + "OK")
    success += 1
else:
    log_reporte(Fore.RED + "FALTAN ARCHIVOS")
    fail += 1
    errores += 1

# === Diagnóstico de alineamiento de tablas y columnas clave en PostgreSQL ===
log_reporte("\n[EXTRA] Diagnóstico de tablas y columnas clave en PostgreSQL:")
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    log_reporte(Fore.RED + "psycopg2 no está instalado. Ejecuta: pip install psycopg2-binary")
    errores += 1
    sys.exit(1)

# Cargar variables de entorno para conexión (puedes ajustar si usas otro sistema)

# --- Cargar credenciales PostgreSQL desde DATABASE_URL ---
import dotenv
import re
dotenv.load_dotenv()
def parse_database_url(url):
    # Formato: postgresql://usuario:password@host:puerto/dbname
    regex = r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/([^/?]+)"
    m = re.match(regex, url)
    if not m:
        return None
    return {
        'user': m.group(1),
        'password': m.group(2),
        'host': m.group(3),
        'port': m.group(4) or '5432',
        'dbname': m.group(5)
    }
PG_CREDS = None
if 'DATABASE_URL' in os.environ:
    PG_CREDS = parse_database_url(os.environ['DATABASE_URL'])
if not PG_CREDS:
    print(Fore.RED + '[ERROR] No se pudo extraer credenciales de PostgreSQL desde DATABASE_URL en .env')
    sys.exit(1)
PG_HOST = PG_CREDS['host']
PG_DB = PG_CREDS['dbname']
PG_USER = PG_CREDS['user']
PG_PASS = PG_CREDS['password']
PG_PORT = PG_CREDS['port']


# Definición de tablas clave y tipos esperados (dict: columna -> tipo SQL)
tablas_clave = {
    'productos': {
        'id': 'integer', 'nombre': 'character varying', 'stock': 'integer', 'costo_unitario': 'numeric',
        'margen_porcentaje': 'numeric', 'precio_sugerido': 'numeric'
    },
    'compras': {
        'id': 'integer', 'producto_id': 'integer', 'cantidad': 'integer', 'costo_unitario': 'numeric', 'fecha': 'date'
    },
    'ventas': {
        'id': 'integer', 'producto_id': 'integer', 'cantidad': 'integer', 'precio_unitario': 'numeric',
        'costo_unitario': 'numeric', 'ganancia_unitaria': 'numeric', 'fecha': 'date'
    },
    'usuarios': {
        'id': 'integer', 'nombre': 'character varying', 'email': 'character varying'
    },
    'gastos': {
        'id': 'integer', 'nombre': 'character varying', 'monto': 'numeric', 'fecha': 'date'
    },
    'activos': {
        'id': 'integer', 'nombre': 'character varying', 'valor': 'numeric'
    },
    'accounts': {
        'id': 'integer', 'name': 'character varying', 'type': 'character varying'
    },
    'journal_entries': {
        'id': 'integer', 'fecha': 'date', 'descripcion': 'character varying'
    },
    'journal_lines': {
        'id': 'integer', 'journal_entry_id': 'integer', 'account_id': 'integer', 'debe': 'numeric', 'haber': 'numeric'
    },
    'inventory_movements': {
        'id': 'integer', 'producto_id': 'integer', 'cantidad': 'integer', 'fecha': 'date'
    },
    'plan_cuentas': {
        'id': 'integer', 'codigo': 'character varying', 'nombre': 'character varying'
    },
    'asientos_contables': {
        'id': 'integer', 'fecha': 'date', 'descripcion': 'character varying'
    },
    'lineas_asiento': {
        'id': 'integer', 'asiento_id': 'integer', 'cuenta_id': 'integer', 'debe': 'numeric', 'haber': 'numeric'
    },
    'movimientos_contables': {
        'id': 'integer', 'cuenta_id': 'integer', 'monto': 'numeric', 'fecha': 'date'
    },
    'operaciones': {
        'id': 'integer', 'tipo': 'character varying', 'fecha': 'date'
    }
}

try:
    conn = psycopg2.connect(
        host=PG_HOST,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        port=PG_PORT
    )
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tablas_existentes = set([row[0] for row in cur.fetchall()])
    for tabla, columnas in tablas_clave.items():
        if tabla in tablas_existentes:
            cur.execute(sql.SQL("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s;"), [tabla])
            cols_info = {row[0]: row[1] for row in cur.fetchall()}
            faltantes = [c for c in columnas if c not in cols_info]
            tipo_mal = [c for c in columnas if c in cols_info and columnas[c] != cols_info[c]]
            if not faltantes and not tipo_mal:
                log_reporte(Fore.GREEN + f"[OK] {tabla}: Todas las columnas clave presentes y tipos correctos.")
            else:
                msg = f"[WARNING] {tabla}: "
                if faltantes:
                    msg += f"Faltan columnas: {faltantes}. "
                if tipo_mal:
                    detalles = [f"{c} (esperado: {columnas[c]}, real: {cols_info[c]})" for c in tipo_mal]
                    msg += f"Tipos incorrectos: {detalles}"
                log_reporte(Fore.YELLOW + msg)
                warnings += 1
        else:
            log_reporte(Fore.RED + f"[ERROR] {tabla}: Tabla no existe en la base de datos.")
            errores += 1
    cur.close()
    conn.close()
except Exception as e:
    log_reporte(Fore.RED + f"[ERROR] No se pudo conectar o consultar PostgreSQL: {e}")
    errores += 1

# 3. Validación de pg_dump en PATH
print("[3/6] pg_dump en PATH: ", end="")
def is_pg_dump_in_path():
    for path in os.environ["PATH"].split(os.pathsep):
        exe = os.path.join(path, "pg_dump.exe")
        if os.path.isfile(exe):
            return exe
    return None
pg_dump_path = is_pg_dump_in_path()
if pg_dump_path:
    log_reporte(Fore.GREEN + f"OK ({pg_dump_path})")
    success += 1
else:
    log_reporte(Fore.RED + "NO ENCONTRADO")
    fail += 1
    errores += 1

# 4. Validación de conexión a la base de datos
print("[4/6] Conexión a base de datos: ", end="")
try:
    import psycopg2
    import dotenv
    dotenv.load_dotenv(".env.production")
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        conn = psycopg2.connect(db_url)
        conn.close()
        log_reporte(Fore.GREEN + "OK")
        success += 1
    else:
        log_reporte(Fore.RED + "NO CONFIGURADA")
        fail += 1
        errores += 1
except Exception as e:
    log_reporte(Fore.RED + f"ERROR: {e}")
    fail += 1
    errores += 1

# 5. Validación de archivos críticos
print("[5/6] Archivos críticos (backup.py, scripts de arranque): ", end="")
archivos = [
    "backend/utils/backup.py",
    "scripts/backup_automatizado.py",
    "arrancar_server_produccion.bat",
    "automatizar_puesta_en_marcha.bat"
]
missing = [f for f in archivos if not os.path.isfile(f)]
if not missing:
    log_reporte(Fore.GREEN + "OK")
    success += 1
else:
    log_reporte(Fore.RED + f"FALTAN: {', '.join(missing)}")
    fail += 1
    errores += 1

# 6. Simulación de arranque de servidor
print("[6/6] Simulación de arranque de servidor: ", end="")
try:
    spec = importlib.util.spec_from_file_location("run_web", "run_web.py")
    if spec and spec.loader:
        run_web = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_web)
        log_reporte(Fore.GREEN + "OK (importación exitosa)")
        success += 1
    else:
        log_reporte(Fore.YELLOW + "NO ENCONTRADO, se omite")
        warnings += 1
except Exception as e:
    log_reporte(Fore.RED + f"ERROR: {e}")
    fail += 1
    errores += 1


# Resumen final
log_reporte("\n==============================")
log_reporte(f" Pruebas exitosas: {success}/{TOTAL_TESTS}")
porcentaje = int((success / TOTAL_TESTS) * 100)
if porcentaje == 100:
    color = Fore.GREEN
elif porcentaje >= 70:
    color = Fore.YELLOW
else:
    color = Fore.RED
log_reporte(f" Estado general: {color}{porcentaje}%{Style.RESET_ALL}")
log_reporte(f"Advertencias: {warnings} | Errores: {errores}")
log_reporte("==============================\n")

# Guardar reporte en archivo
try:
    with open("diagnostico_semaforo_report.txt", "w", encoding="utf-8") as f:
        f.write(f"Reporte diagnóstico ZIONX ERP - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for line in reporte:
            # Eliminar códigos de color para el archivo
            clean = line.replace(Fore.GREEN, "").replace(Fore.RED, "").replace(Fore.YELLOW, "").replace(Style.RESET_ALL, "")
            f.write(clean + "\n")
    print(Fore.CYAN + "\n[INFO] Reporte guardado en diagnostico_semaforo_report.txt\n")
except Exception as e:
    print(Fore.RED + f"[ERROR] No se pudo guardar el reporte: {e}")
