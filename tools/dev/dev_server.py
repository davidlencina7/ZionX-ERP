"""
🚀 ZionX ERP - Servidor de Desarrollo para Modo Operativo

Este script inicia el servidor Flask en modo desarrollo para probar
el módulo operativo (Compras, Ventas, Gastos, Inversiones).

Uso:
    python dev_server.py

Acceso:
    http://localhost:5000/operaciones

Características:
    - Hot-reload automático al detectar cambios en código
    - Debug mode activado
    - CSRF habilitado
    - Logging detallado en consola
    - Puerto 5000
"""
import os
import sys
from pathlib import Path

# Agregar la raíz del proyecto al sys.path para que se pueda importar 'backend' correctamente
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Asegurar que estamos en modo desarrollo
os.environ['MODE'] = 'dev'
os.environ['DEBUG'] = 'True'
os.environ['DEVELOPMENT_MODE'] = 'True'

# Configurar logging para desarrollo
from backend.utils.logging_config import configurar_logging
configurar_logging(nivel_consola='DEBUG', nivel_archivo='DEBUG')

from backend import create_app


def main():
    """Función principal para iniciar el servidor en modo desarrollo"""
    
    print("=" * 80)
    print(" 🚀 ZionX ERP - MODO OPERATIVO")
    print("=" * 80)
    print()
    print("SERVIDOR DE DESARROLLO")
    print()
    print("📋 Módulos disponibles:")
    print("   • Compras de mercadería")
    print("   • Ventas de productos")
    print("   • Gastos operativos")
    print("   • Inversiones / Aportes de capital")
    print()
    print("📊 Reportes disponibles:")
    print("   • Inventario valorizado (Promedio Ponderado Móvil)")
    print("   • Libro diario (asientos contables)")
    print("   • Balance general (estado financiero)")
    print()
    print("🌐 URL Principal:")
    print("   → http://localhost:5000/operaciones")
    print()
    print("🔧 Configuración:")
    print(f"   • Modo: DESARROLLO")
    print(f"   • Debug: ACTIVO")
    print(f"   • Hot-reload: ACTIVO")
    print("   • Base de datos: PostgreSQL")
    print()
    print("=" * 80)
    print()
    print("Presiona CTRL+C para detener el servidor")
    print()
    print("=" * 80)
    print()
    
    # Crear la aplicación Flask
    app = create_app('development')
    
    # Ejecutar servidor en modo desarrollo
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True,
        extra_files=None,  # Flask detectará automáticamente los cambios
        threaded=True
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✅ Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error al iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
