import importlib
import psycopg2
from psycopg2 import sql

# Configuración de diagnóstico de base de datos
TABLAS_REQUERIDAS = {
    'usuarios': [
        'id', 'username', 'nombre_completo', 'rol', 'password_hash', 'email', 'activo', 'tema_preferido', 'fecha_creacion', 'ultimo_acceso',
        'nombre', 'fecha'
    ],
    'productos': [
        'id', 'nombre', 'stock', 'costo_unitario', 'margen_porcentaje', 'precio_sugerido',
        'especificaciones', 'precio', 'fecha'
    ],
    'compras': [
        'id', 'producto_id', 'cantidad', 'costo_unitario', 'fecha', 'mes_contable',
        'nombre'
    ],
    'ventas': [
        'id', 'producto_id', 'cantidad', 'precio_unitario', 'costo_unitario', 'ganancia_unitaria', 'fecha', 'forma_pago', 'mes_contable',
        'nombre'
    ],
    'gastos': [
        'id', 'concepto', 'monto', 'categoria', 'fecha', 'mes_contable', 'usuario_id', 'notas', 'fecha_registro',
        'descripcion', 'created_at', 'nombre'
    ],
    'activos': [
        'id', 'nombre', 'valor_adquisicion', 'fecha_adquisicion', 'categoria', 'descripcion', 'vida_util_meses', 'valor_residual', 'depreciacion_mensual', 'activo', 'usuario_id', 'fecha_registro',
        'vida_util_anos', 'estado', 'user_id', 'created_at', 'updated_at', 'valor'
    ],
    'movimientos_contables': [
        'id', 'mes_contable', 'tipo', 'categoria', 'concepto', 'monto', 'fecha_movimiento', 'referencia_tabla', 'referencia_id', 'usuario_id', 'fecha_registro',
        'debe', 'haber', 'descripcion', 'nombre', 'fecha', 'cuenta_id'
    ],
    'accounts': [
        'id', 'code', 'name', 'account_type', 'nature', 'subtype', 'parent_id', 'active', 'description', 'fecha_registro',
        'created_at', 'nombre', 'fecha', 'type'
    ],
    'journal_entries': [
        'id', 'date', 'description', 'entry_type', 'reference_table', 'reference_id', 'user_id', 'created_at',
        'fecha', 'descripcion'
    ],
    'journal_lines': [
        'id', 'journal_entry_id', 'account_id', 'debit', 'credit', 'description',
        'debe', 'haber'
    ],
    'inventory_movements': [
        'id', 'producto_id', 'movement_type', 'cantidad', 'costo_unitario', 'fecha', 'reference_table', 'reference_id', 'descripcion', 'stock_anterior', 'stock_nuevo', 'costo_promedio_anterior', 'costo_promedio_nuevo'
    ],
}

def diagnostico_postgres():
    print("\n=== Diagnóstico de PostgreSQL ===\n")
    import os
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("🔴 No se encontró la variable de entorno DATABASE_URL.")
        return False
    try:
        conn = psycopg2.connect(db_url)
        print("🟢 Conexión a PostgreSQL exitosa.")
    except Exception as e:
        print(f"🔴 Error de conexión a PostgreSQL: {e}")
        return False
    cur = conn.cursor()
    ok = True
    for tabla, columnas in TABLAS_REQUERIDAS.items():
        try:
            cur.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier(tabla)))
            colnames = [desc[0] for desc in cur.description]
            faltantes = [col for col in columnas if col not in colnames]
            extras = [col for col in colnames if col not in columnas]
            if faltantes:
                print(f"🟡 Tabla '{tabla}': Faltan columnas: {faltantes}")
                ok = False
            else:
                print(f"🟢 Tabla '{tabla}' OK")
            if extras:
                print(f"⚠️  Tabla '{tabla}': Columnas extra detectadas: {extras}")
        except Exception as e:
            print(f"🔴 Tabla '{tabla}' no encontrada o inaccesible: {e}")
            ok = False
    cur.close()
    conn.close()
    if ok:
        print("\n✅ Estructura de base de datos verificada correctamente.\n")
    else:
        print("\n❌ Problemas detectados en la estructura de la base de datos. Corrige antes de continuar.\n")
    return ok

# Dependencias críticas para el ERP
DEPENDENCIAS_CRITICAS = [
    'flask',
    'flask_login',
    'flask_wtf',
    'reportlab',
    'bcrypt',
    'waitress',
    'sqlalchemy',
    'dotenv',  # Corrección aquí
    'psycopg2',
    'wtforms',
]

def verificar_dependencias():
    print("\nVerificando dependencias críticas...\n")
    faltantes = []
    for dep in DEPENDENCIAS_CRITICAS:
        try:
            importlib.import_module(dep)
            print(f"🟢 {dep}")
        except ImportError:
            print(f"🔴 {dep}")
            faltantes.append(dep)
    porcentaje = int(100 * (len(DEPENDENCIAS_CRITICAS) - len(faltantes)) / len(DEPENDENCIAS_CRITICAS))
    if porcentaje == 100:
        print("\n✅ Todas las dependencias críticas están instaladas (100%)\n")
    elif porcentaje >= 80:
        print(f"\n🟡 {porcentaje}% de dependencias críticas instaladas. Faltan: {', '.join(faltantes)}\n")
    else:
        print(f"\n🔴 Solo {porcentaje}% de dependencias críticas instaladas. Faltan: {', '.join(faltantes)}\n")
    return faltantes, porcentaje

def instalar_dependencias(faltantes):
    import subprocess
    print(f"\nIntentando instalar automáticamente: {' '.join(faltantes)}\n")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + faltantes)
        print("\n✅ Instalación automática completada. Reinicia el script para continuar.")
    except Exception as e:
        print(f"\n❌ Error al instalar dependencias automáticamente: {e}")
        print("Instala manualmente con: pip install " + ' '.join(faltantes))
    input("Presiona ENTER para salir...")
    sys.exit(1)
"""
PIU PIU Mini-ERP - Aplicacion Web Standalone
Inicia el servidor Flask y abre el navegador automaticamente
"""

import os
import sys
import time
import threading
import webbrowser
from pathlib import Path

# Configurar rutas
if getattr(sys, 'frozen', False):
    # Ejecutando como ejecutable empaquetado
    project_root = Path(sys._MEIPASS)
    os.chdir(sys._MEIPASS)
else:
    # Ejecutando como script Python
    project_root = Path(__file__).parent

sys.path.insert(0, str(project_root))

# Configurar modo produccion para ejecutable
os.environ['MODE'] = 'prod'
# Eliminado: solo PostgreSQL

from backend.utils.logging_config import configurar_logging
configurar_logging(nivel_consola='WARNING', nivel_archivo='INFO')

from backend import create_app


def open_browser():
    """Abre el navegador despues de 2 segundos"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')


def main():
    # Diagnóstico automático de PostgreSQL
    if not diagnostico_postgres():
        input("Presiona ENTER para salir...")
        sys.exit(1)

    # Verificar entorno virtual activo
    if sys.prefix == sys.base_prefix:
        print("\n⚠️  ADVERTENCIA: No estás usando el entorno virtual (.venv). Actívalo antes de continuar para evitar conflictos de dependencias.")
        input("Presiona ENTER para salir...")
        sys.exit(1)

    # Verificar modo de ejecución
    mode = os.environ.get('MODE', '').lower()
    if mode not in ('prod', 'production', 'dev', 'development'):
        print(f"\n⚠️  ADVERTENCIA: El modo de ejecución (MODE) no está definido o es inválido: '{mode}'. Usa 'prod' o 'dev'.")
        input("Presiona ENTER para salir...")
        sys.exit(1)
    if mode in ('dev', 'development'):
        print("\n🟡 MODO DESARROLLO: El servidor se ejecutará en modo desarrollo. No usar en producción.")
    else:
        print("\n🟢 MODO PRODUCCIÓN: El servidor se ejecutará en modo seguro.")

    # Verificar si el puerto 5000 está ocupado
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5000))
    if result == 0:
        print("\n❌ Error: El puerto 5000 ya está en uso. Cierra la aplicación que lo esté usando o cambia el puerto.")
        sock.close()
        input("Presiona ENTER para salir...")
        sys.exit(1)
    sock.close()

    # Verificar dependencias antes de iniciar
    faltantes, porcentaje = verificar_dependencias()
    if faltantes:
        print("\nNo se puede iniciar el servidor hasta instalar todas las dependencias críticas.")
        opcion = input("¿Deseas que las instale automáticamente? (s/n): ").strip().lower()
        if opcion == 's':
            instalar_dependencias(faltantes)
        else:
            print("Ejecuta: pip install " + ' '.join(faltantes))
            input("Presiona ENTER para salir...")
            sys.exit(1)

    try:
        # Crear la aplicacion Flask
        app = create_app()
        from backend.core.version import APP_NAME, APP_NAME_FULL
        print("=" * 60)
        print(f"{APP_NAME_FULL} ({APP_NAME}) - Sistema Web")
        print("=" * 60)
        print("Iniciando servidor...")
        print("Se abrirá el navegador automáticamente")
        print("=" * 60)
        # Abrir navegador en thread separado
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        # Importar servidor WSGI
        try:
            from waitress import serve
            print("\n✅ Servidor iniciado en http://localhost:5000")
            print("Cierra esta ventana para detener el servidor\n")
            serve(app, host='0.0.0.0', port=5000, threads=4)
        except ImportError:
            # Fallback a Flask development server
            print("\n✅ Servidor iniciado en http://localhost:5000")
            print("Presiona CTRL+C para detener el servidor\n")
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n✅ Servidor detenido correctamente")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        input("Presiona ENTER para salir...")
        sys.exit(1)


if __name__ == '__main__':
    main()
