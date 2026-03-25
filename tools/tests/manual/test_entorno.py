"""
Test rápido del entorno de desarrollo
Verifica que el servidor pueda iniciarse correctamente
"""
import sys
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Verificar que los imports funcionen"""
    print("🔍 Verificando imports...")
    
    try:
        from backend import create_app
        print("   ✅ backend.create_app")
    except ImportError as e:
        print(f"   ❌ Error importando backend: {e}")
        return False
    
    try:
        from backend.config.settings import MODE, DEBUG
        print("   ✅ backend.config.settings")
        print(f"      MODE={MODE}, DEBUG={DEBUG}")
    except ImportError as e:
        print(f"   ❌ Error importando settings: {e}")
        return False
    
    try:
        from backend.services.productos_service import ProductosService
        print("   ✅ backend.services")
    except ImportError as e:
        print(f"   ❌ Error importando services: {e}")
        return False
    
    return True


def test_app_creation():
    """Verificar que la app Flask se cree correctamente"""
    print("\n🏗️  Verificando creación de app Flask...")
    
    try:
        from backend import create_app
        app = create_app('development')
        print("   ✅ App Flask creada correctamente")
        print(f"      Debug: {app.config.get('DEBUG')}")
        print(f"      Testing: {app.config.get('TESTING')}")
        return True
    except Exception as e:
        print(f"   ❌ Error creando app: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """Verificar acceso a base de datos"""
    print("\n💾 Verificando base de datos...")
    
    try:
        from backend.database.connection import DatabaseConnection
        db = DatabaseConnection.get_instance()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Contar tablas
        # Eliminado: solo PostgreSQL
        count = cursor.fetchone()[0]
        print(f"   ✅ Base de datos accesible ({count} tablas)")
        
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Error accediendo a BD: {e}")
        return False


def main():
    """Ejecutar todas las verificaciones"""
    print("="*60)
    print("VERIFICACIÓN DE ENTORNO DE DESARROLLO")
    print("="*60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: App creation
    results.append(("App Flask", test_app_creation()))
    
    # Test 3: Database
    results.append(("Base de Datos", test_database()))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        icon = "✅" if result else "❌"
        print(f"{icon} {name}")
    
    print(f"\n{passed}/{total} verificaciones pasadas")
    
    if passed == total:
        print("\n✅ ENTORNO LISTO PARA DESARROLLO")
        print("\nPuedes iniciar el servidor con:")
        print("   python dev_server.py")
        print("\nO usando el batch:")
        print("   iniciar_dev_web.bat")
    else:
        print("\n⚠️  ALGUNOS PROBLEMAS DETECTADOS")
        print("Revisa los errores anteriores")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error durante verificación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
