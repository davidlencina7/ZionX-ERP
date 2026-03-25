
import os
import sys
from pathlib import Path

# Cargar variables de entorno de producción
try:
    from dotenv import load_dotenv
    dotenv_path = Path(__file__).parent.parent.parent / '.env.production'
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        print("\033[92m[OK] .env.production cargado correctamente ✅\033[0m")
    else:
        print("\033[93m[WARN] No se encontró .env.production\033[0m")
except Exception as e:
    print(f"\033[91m[ERROR] No se pudo cargar .env.production: {e}\033[0m")

# Agregar la raíz del proyecto al sys.path para importar 'backend'
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
print("\033[92m[OK] sys.path configurado ✅\033[0m")

from backend import create_app

def main():
    print("=" * 80)
    print(" ZIONX ERP - MODO OPERATIVO (PRODUCCIÓN)")
    print("=" * 80)
    print("\033[94m--- INFORMACIÓN DE ENTORNO ---\033[0m")
    venv = os.environ.get('VIRTUAL_ENV', None)
    print(f"\033[96m[INFO] Entorno virtual: {venv if venv else 'No detectado'}\033[0m")
    print(f"\033[96m[INFO] Python ejecutable: {sys.executable}\033[0m")
    print(f"\033[96m[INFO] Ruta actual (cwd): {os.getcwd()}\033[0m")
    print(f"\033[96m[INFO] sys.path[0]: {sys.path[0]}\033[0m")
    print(f"\033[96m[INFO] Usuario del sistema: {os.environ.get('USERNAME', os.environ.get('USER', 'Desconocido'))}\033[0m")
    print(f"\033[96m[INFO] Plataforma: {sys.platform}\033[0m")
    print(f"\033[96m[INFO] DATABASE_URL: {os.environ.get('DATABASE_URL', 'No definida')}\033[0m")
    print(f"\033[96m[INFO] SECRET_KEY: {'Definida' if os.environ.get('SECRET_KEY') else 'No definida'}\033[0m")
    print("\033[94m-----------------------------\033[0m\n")
    print("\033[92m[OK] Iniciando servidor WSGI para entorno productivo... ✅\033[0m")
    print()
    app = create_app('production')
    print("\033[92m[OK] App Flask creada y configurada ✅\033[0m")
    print("[INFO] Usando base de datos: PostgreSQL (DATABASE_URL)")
    # Espera a que un servidor WSGI (como Gunicorn o Waitress) lo ejecute
    return app

from waitress import serve

if __name__ == '__main__':
    app = main()
    host = '0.0.0.0'
    port = 8000
    print("\033[92m[OK] Servidor Waitress listo para recibir conexiones ✅\033[0m")
    print(f"\033[96m[INFO] Host: {host}\033[0m")
    print(f"\033[96m[INFO] Puerto: {port}\033[0m")
    import socket
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = 'localhost'
    print(f"\033[92m[URL Local]   http://127.0.0.1:{port}/\033[0m")
    print(f"\033[92m[URL Red]    http://{local_ip}:{port}/\033[0m")
    print(f"\033[93m[NOTA] Si usas Docker o WSL, revisa la IP de tu contenedor o máquina virtual.\033[0m")
    serve(app, host=host, port=port)
