import sys
import os
from datetime import datetime
from io import StringIO
import traceback

# 1. Definir BASE_DIR primero
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 2. Agregar al path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 3. Cargar variables de entorno
if not os.environ.get('DATABASE_URL'):
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(BASE_DIR, '.env.production')
        load_dotenv(env_path)
        print(f"🟢 .env cargado desde: {env_path}")
    except ImportError:
        print('⚠️ python-dotenv no instalado (pip install python-dotenv)')


def diagnostico_sincronizacion():
    buffer = StringIO()

    try:
        buffer.write('--- Verificación de configuración de base de datos ---\n')

        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            error_msg = (
                '[ERROR] 🔴 DATABASE_URL no definida\n'
                'SUGERENCIA: Defina la variable de entorno DATABASE_URL en el sistema o en el archivo .env.production.\n'
            )
            buffer.write(error_msg)
            print(error_msg)
            return
        else:
            buffer.write(f'🟢 DATABASE_URL detectada\n\n')

        # --- Validar tabla productos ---
        try:
            from backend.database.connection import DatabaseConnection

            db = DatabaseConnection.get_instance()
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM productos")
            total = cursor.fetchone()[0]

            if total == 0:
                error_msg = (
                    '[ERROR] 🔴 Tabla productos vacía\n'
                    'SUGERENCIA: Verifique que la tabla productos esté correctamente poblada. Importe los productos necesarios en la base de datos.\n'
                )
                buffer.write(error_msg)
                print(error_msg)
                return
            else:
                buffer.write(f'🟢 {total} productos encontrados\n\n')

            conn.close()

        except Exception as e:
            error_msg = (
                f'[ERROR] 🔴 Error DB: {e}\n'
                'SUGERENCIA: Verifique la conexión a la base de datos y que la tabla productos exista.\n'
            )
            buffer.write(error_msg)
            print(error_msg)
            return

        # --- Servicios ---
        from backend.services.inventario_service import InventarioService
        from backend.services.gerencial_service import GerencialService
        from backend.services.productos_service import ProductosService


        inventario = InventarioService()
        gerencial = GerencialService()
        productos_service = ProductosService()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        buffer.write(
            f"==== DIAGNÓSTICO DE SINCRONIZACIÓN DE ÁREAS ====\n"
            f"Fecha: {now}\n\n"
        )

        inventario_data = inventario.obtener_inventario_valorizado_total()
        productos_inv = {str(p['id']): p for p in inventario_data.get('productos', [])}

        panel = gerencial.construir_panel_data()
        productos_panel = {p['nombre']: p for p in panel.get('productos_costo', [])}

        productos_precios = {
            str(p.id): p for p in productos_service.listar_productos()
        }

        inconsistencias = 0
        faltantes = []

        buffer.write('--- Chequeo por producto ---\n')

        for pid, prod_inv in productos_inv.items():
            nombre = prod_inv['nombre']

            stock_inv = float(prod_inv['stock'])
            costo_inv = float(prod_inv['costo_promedio'])

            prod_panel = productos_panel.get(nombre)
            prod_precio = productos_precios.get(pid)

            stock_panel = float(prod_panel['stock']) if prod_panel else None
            costo_panel = float(prod_panel['costo_promedio']) if prod_panel else None

            stock_precio = float(prod_precio.stock) if prod_precio else None
            costo_precio = float(prod_precio.costo_unitario) if prod_precio else None

            # --- Comparación STOCK ---
            if (stock_panel is not None and abs(stock_inv - stock_panel) > 0.01) or \
               (stock_precio is not None and abs(stock_inv - stock_precio) > 0.01):

                error_msg = (
                    f"[ERROR] 🔴 STOCK desincronizado: {nombre} | Inv={stock_inv}, Panel={stock_panel}, Precios={stock_precio}\n"
                    f"SUGERENCIA: Revise el stock del producto '{nombre}' en las áreas de Inventario, Panel Gerencial - ZionX ERP y Precios. Corrija la discrepancia para mantener la sincronización.\n"
                )
                buffer.write(error_msg)
                inconsistencias += 1

            # --- Comparación COSTO ---
            if (costo_panel is not None and abs(costo_inv - costo_panel) > 0.01) or \
               (costo_precio is not None and abs(costo_inv - costo_precio) > 0.01):

                error_msg = (
                    f"[ERROR] 🔴 COSTO desincronizado: {nombre} | Inv={costo_inv}, Panel={costo_panel}, Precios={costo_precio}\n"
                    f"SUGERENCIA: Revise el costo promedio del producto '{nombre}' en Inventario, Panel Gerencial - ZionX ERP y Precios. Unifique el valor para evitar inconsistencias.\n"
                )
                buffer.write(error_msg)
                inconsistencias += 1

            # --- Faltantes ---
            if prod_precio is None:
                faltantes.append(nombre)

        # --- Resultados ---
        if not inconsistencias and not faltantes:
            buffer.write('🟢 Todo sincronizado\n')

        if faltantes:
            buffer.write('\n[ERROR] 🔴 Productos sin gestión de precios:\n')
            for f in faltantes:
                buffer.write(f" - {f}\n")
            buffer.write('SUGERENCIA: Agregue estos productos al sistema de gestión de precios para completar la sincronización.\n')

        buffer.write(f"\nTOTAL inconsistencias: {inconsistencias}\n")

        print(buffer.getvalue())

    except Exception as e:
        error_msg = (
            f'[ERROR] 🔴 ERROR GENERAL: {e}\n'
            f'SUGERENCIA: Revise el traceback para más detalles y corrija el error reportado.\n{traceback.format_exc()}\n'
        )
        print(error_msg)


def main():
    print('--- DIAGNÓSTICO ZIONX ERP ---')
    diagnostico_sincronizacion()


if __name__ == '__main__':
    main()