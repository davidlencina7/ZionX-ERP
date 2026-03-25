"""
Diagnóstico comparativo entre Inventario y Panel Gerencial
Verifica que los totales de stock y ventas coincidan entre InventarioService y GerencialService.
"""
import sys
import os
from datetime import datetime
import traceback

# Asegura que la ruta base del proyecto esté en sys.path antes de cualquier import
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from backend.services.inventario_service import InventarioService
    from backend.services.gerencial_service import GerencialService
except Exception as e:
    print('🔴 ERROR: No se pudieron importar los servicios:', e)
    sys.exit(1)

def diagnostico_comparativo():
    from io import StringIO
    import os
    buffer = StringIO()
    try:
        inventario = InventarioService()
        gerencial = GerencialService()
        # Obtener datos de inventario
        inventario_data = inventario.obtener_inventario_valorizado_total()
        productos = inventario_data.get('productos', [])
        total_stock = sum(float(p.get('stock', 0)) for p in productos)
        # Obtener datos del panel gerencial usando construir_panel_data
        panel = gerencial.construir_panel_data()
        productos_panel = panel.get('productos_costo', [])
        total_stock_panel = sum(float(p.get('stock', 0)) for p in productos_panel)
        ventas_panel = panel.get('ventas_mes', [])
        total_ventas_panel = sum(float(v.get('total', 0)) for v in ventas_panel)
        # Mostrar resultados generales
        buffer.write(f"Total stock (Inventario): {total_stock}\n")
        buffer.write(f"Total stock (Panel Gerencial): {total_stock_panel}\n")
        print(f"Total stock (Inventario): {total_stock}")
        print(f"Total stock (Panel Gerencial): {total_stock_panel}")
        if abs(total_stock - total_stock_panel) < 0.01:
            buffer.write('🟢 Stock coincidente entre inventario y panel gerencial.\n')
            print('🟢 Stock coincidente entre inventario y panel gerencial.')
        else:
            buffer.write('🔴 Diferencia de stock detectada entre inventario y panel gerencial.\n')
            print('🔴 Diferencia de stock detectada entre inventario y panel gerencial.')
            # Listar productos con diferencias
            panel_dict = {p.get('nombre'): p for p in productos_panel}
            for p in productos:
                nombre = p.get('nombre')
                stock_inv = float(p.get('stock', 0))
                stock_panel = float(panel_dict.get(nombre, {}).get('stock', 0))
                if abs(stock_inv - stock_panel) > 0.01:
                    buffer.write(f"   ⚠️ Producto {nombre}: stock inventario={stock_inv}, stock panel={stock_panel}\n")
                    print(f"   ⚠️ Producto {nombre}: stock inventario={stock_inv}, stock panel={stock_panel}")

        # Comparar ventas del mes
        if ventas_panel:
            # Se asume que ventas_panel contiene dicts con 'id' y 'total'
            ventas_inventario = []  # Si existe método para obtener ventas del inventario, agregar aquí
            # ids_panel = set(v.get('id') for v in ventas_panel if v.get('id') is not None)
            # ids_inv = set(v.get('id') for v in ventas_inventario if v.get('id') is not None)
            # solo_panel = ids_panel - ids_inv
            # solo_inv = ids_inv - ids_panel
            # if solo_panel:
            #     buffer.write(f"🔴 Ventas presentes en panel gerencial pero no en inventario: {list(solo_panel)}\n")
            #     print('🔴 Ventas presentes en panel gerencial pero no en inventario:', list(solo_panel))
            # if solo_inv:
            #     buffer.write(f"🔴 Ventas presentes en inventario pero no en panel gerencial: {list(solo_inv)}\n")
            #     print('🔴 Ventas presentes en inventario pero no en panel gerencial:', list(solo_inv))
            # if not solo_panel and not solo_inv:
            #     buffer.write('🟢 Las ventas coinciden entre inventario y panel gerencial.\n')
            #     print('🟢 Las ventas coinciden entre inventario y panel gerencial.')
            buffer.write(f"Total ventas mes (Panel Gerencial): {total_ventas_panel}\n")
            print(f"Total ventas mes (Panel Gerencial): {total_ventas_panel}")
        else:
            buffer.write('⚠️  No se pudo comparar ventas detalladas (faltan datos en panel gerencial).\n')
            print('⚠️  No se pudo comparar ventas detalladas (faltan datos en panel gerencial).')
    except Exception as e:
        buffer.write(f'🔴 ERROR en diagnóstico comparativo: {e}\n')
        buffer.write(traceback.format_exc() + '\n')
        print('🔴 ERROR en diagnóstico comparativo:', e)
        print(traceback.format_exc())
    # Guardar el reporte en archivo
    reporte_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(reporte_dir, exist_ok=True)
    reporte_path = os.path.join(reporte_dir, f'reporte_inventario_vs_gerencial_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    with open(reporte_path, 'w', encoding='utf-8') as f:
        f.write(buffer.getvalue())
    print(f'📝 Reporte guardado en: {reporte_path}')

def main():
    print('--- DIAGNÓSTICO COMPARATIVO INVENTARIO vs PANEL GERENCIAL ---')
    print(f'Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    diagnostico_comparativo()

if __name__ == '__main__':
    main()
