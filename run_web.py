"""
Script para ejecutar el servidor web Flask del Mini-ERP PIU PIU

Uso:
    python run_web.py

Variables de entorno:
    MODE=dev        Modo desarrollo (por defecto)
    MODE=prod       Modo producción
    MODE=test       Modo testing
"""

import os
import sys
from pathlib import Path

# Agregar la raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configurar logging ANTES de importar la app
from backend.utils.logging_config import configurar_logging

# Configurar según modo

def get_mode():
    # Por defecto, forzar modo producción salvo que se indique explícitamente otro modo
    mode = os.getenv('MODE', 'prod')
    if mode == 'cli':
        mode = 'prod'
    return mode

mode = get_mode()
if mode == 'prod':
    configurar_logging(nivel_consola='WARNING', nivel_archivo='INFO')
else:
    configurar_logging(nivel_consola='INFO', nivel_archivo='INFO')

from backend import create_app


def main():
    """Función principal para iniciar el servidor web"""
    
    # Crear la aplicación Flask
    app = create_app()
    print("\n🟡 Recuerda: realiza un backup manual antes de trabajar en producción.")
    print("    Ejecuta: python scripts/backup_automatizado.py\n")

    # Usar el modo global leído al inicio
    global mode
    if mode == 'dev':
        print("=" * 60)
        print("ZionX ERP - Servidor Web")
        print("=" * 60)
        print(f"Modo: {mode.upper()}")
        print("URL local: http://localhost:5000  o  http://127.0.0.1:5000")
        print("Base de datos: PostgreSQL")
        print("=" * 60)
        print("\nPresiona CTRL+C para detener el servidor\n")

        # Ejecutar servidor en modo desarrollo
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )

    elif mode == 'prod':
        print("=" * 60)
        print("ZionX ERP - Servidor Web (PRODUCCIÓN)")
        print("=" * 60)
        print(f"Modo: {mode.upper()}")
        print("URL local: http://localhost:5000  o  http://127.0.0.1:5000")
        print("=" * 60)
        print("\n⚠️  ADVERTENCIA: Modo producción activado")
        print("⚠️  Usa un servidor WSGI (gunicorn, waitress) en producción real\n")

        # Ejecutar servidor en modo producción
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False
        )

    elif mode == 'test':
        print("=" * 60)
        print("ZionX ERP - Servidor Web (TESTING)")
        print("=" * 60)
        print(f"Modo: {mode.upper()}")
        print("=" * 60)

        # Ejecutar servidor en modo testing
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False
        )

    else:
        print(f"❌ Error: Modo '{mode}' no reconocido")
        print("Usa: MODE=dev, MODE=prod o MODE=test")
        sys.exit(1)


if __name__ == '__main__':
    # Arranque normal, sin backup automatizado
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nServidor detenido correctamente")
        sys.exit(0)
    except Exception as e:
        print(f"\nError al iniciar el servidor: {e}")
        sys.exit(1)
