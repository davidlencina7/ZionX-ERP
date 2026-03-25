"""
Blueprint de Dashboard - Vista principal de ZionX ERP
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from datetime import datetime, timedelta
from dataclasses import asdict
from collections import defaultdict

from backend.services.reportes_service import ReportesService
from backend.services.productos_service import ProductosService
from backend.services.ventas_service import VentasService
from backend.services.compras_service import ComprasService

dashboard_bp = Blueprint('dashboard', __name__)


def producto_to_dict(producto):
    """Convertir objeto Producto a diccionario"""
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'stock_actual': producto.stock,
        'stock_minimo': 5,  # Valor por defecto para alertas
        'costo_promedio': producto.costo_unitario,
        'margen_venta': producto.margen_porcentaje
    }


@dashboard_bp.route('/')
@login_required
def index():
    """Vista principal del dashboard"""
    
    try:
        # Inicializar servicios
        reportes_service = ReportesService()
        productos_service = ProductosService()
        ventas_service = VentasService()
        compras_service = ComprasService()
        
        # Obtener datos del día
        reporte_diario = reportes_service.generar_reporte_diario()
        todos_productos = productos_service.obtener_todos_productos()
        # Depuración: imprimir tipos y valores de productos
        import sys
        print("[DEBUG] todos_productos:", todos_productos, file=sys.stderr)
        if len(todos_productos) > 0:
            print("[DEBUG] tipo primer producto:", type(todos_productos[0]), file=sys.stderr)
            print("[DEBUG] primer producto:", todos_productos[0], file=sys.stderr)
        # Filtrar productos con stock bajo manualmente
        productos_bajo_stock = [producto_to_dict(p) for p in todos_productos if hasattr(p, 'stock') and p.stock <= 5]
        
        # Obtener datos para gráficos - últimos 7 días
        fecha_inicio = datetime.now() - timedelta(days=7)
        todas_ventas = ventas_service.listar_ventas()
        todas_compras = compras_service.obtener_todas_compras()
        
        # Agrupar ventas y compras por día
        ventas_por_dia = defaultdict(lambda: {'cantidad': 0, 'total': 0})
        compras_por_dia = defaultdict(lambda: {'cantidad': 0, 'total': 0})
        ventas_por_producto = defaultdict(int)
        
        # Diccionario de productos por ID para lookup eficiente
        productos_dict = {}
        for p in todos_productos:
            # Soporta tanto objetos Producto como diccionarios
            try:
                if isinstance(p, dict):
                    productos_dict[p.get('id')] = p.get('nombre')
                else:
                    productos_dict[p.id] = p.nombre
            except Exception as e:
                print(f"[ERROR] Producto inválido para dict: {p} - {e}", file=sys.stderr)
        print("[DEBUG] productos_dict:", productos_dict, file=sys.stderr)
        
        from datetime import datetime as dt, time as dttime, date as dtdate
        def to_datetime_safe(fecha):
            if isinstance(fecha, str):
                return dt.fromisoformat(fecha.replace('Z', '+00:00'))
            elif isinstance(fecha, dt):
                return fecha
            elif isinstance(fecha, dtdate):
                return dt.combine(fecha, dttime.min)
            else:
                raise ValueError(f"Tipo de fecha inesperado: {type(fecha)}")

        fecha_inicio_dt = to_datetime_safe(fecha_inicio)

        for venta in todas_ventas:
            venta_fecha_dt = to_datetime_safe(venta.fecha)
            if venta_fecha_dt >= fecha_inicio_dt:
                fecha_str = venta_fecha_dt.strftime('%Y-%m-%d')
                ventas_por_dia[fecha_str]['cantidad'] += venta.cantidad
                ventas_por_dia[fecha_str]['total'] += venta.precio_unitario * venta.cantidad
                # Obtener nombre del producto
                producto_nombre = productos_dict.get(venta.producto_id, 'Desconocido')
                ventas_por_producto[producto_nombre] += venta.cantidad

        for compra in todas_compras:
            compra_fecha_dt = to_datetime_safe(compra.fecha)
            if compra_fecha_dt >= fecha_inicio_dt:
                fecha_str = compra_fecha_dt.strftime('%Y-%m-%d')
                compras_por_dia[fecha_str]['cantidad'] += compra.cantidad
                compras_por_dia[fecha_str]['total'] += compra.costo_unitario * compra.cantidad
        
        # Preparar datos para Chart.js (últimos 7 días)
        labels = []
        ventas_data = []
        compras_data = []
        
        for i in range(7):
            fecha = datetime.now() - timedelta(days=6-i)
            fecha_str = fecha.strftime('%Y-%m-%d')
            labels.append(fecha.strftime('%d/%m'))
            ventas_data.append(float(ventas_por_dia[fecha_str]['total']))
            compras_data.append(float(compras_por_dia[fecha_str]['total']))
        
        # Top 5 productos más vendidos
        # Top 5 productos más vendidos
        top_productos = sorted(ventas_por_producto.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Si no hay datos, usar valores por defecto
        if top_productos:
            top_productos_labels = [p[0] for p in top_productos]
            top_productos_data = [p[1] for p in top_productos]
        else:
            top_productos_labels = ['Sin datos']
            top_productos_data = [0]
        
        # Preparar datos para el dashboard
        dashboard_data = {
            'fecha': datetime.now().strftime('%d/%m/%Y'),
            'ventas_cantidad': reporte_diario.get('ventas_cantidad', 0),
            'ganancia_total': reporte_diario.get('ganancia_total', 0.0),
            'compras_cantidad': reporte_diario.get('compras_cantidad', 0),
            'compras_costo': reporte_diario.get('compras_costo', 0.0),
            'stock_total': reporte_diario.get('stock_total', 0),
            'ganancia_acumulada': reporte_diario.get('ganancia_acumulada', 0.0),
            'total_productos': len(todos_productos),
            'productos_bajo_stock': len(productos_bajo_stock),
            'productos_bajo_stock_lista': productos_bajo_stock,
            # Datos para gráficos
            'chart_labels': labels,
            'chart_ventas': ventas_data,
            'chart_compras': compras_data,
            'chart_top_productos_labels': top_productos_labels,
            'chart_top_productos_data': top_productos_data
        }
        
        # Bloque de depuración: imprimir tipos y datos antes de renderizar
        import sys
        print("[DEBUG] dashboard_data type:", type(dashboard_data), file=sys.stderr)
        for k, v in dashboard_data.items():
            print(f"[DEBUG] {k}: type={type(v)}, value={str(v)[:300]}", file=sys.stderr)
        print("[DEBUG] productos_bajo_stock_lista sample:", dashboard_data.get('productos_bajo_stock_lista', None), file=sys.stderr)
        return render_template('dashboard_dict.html', data=dashboard_data)
    
    except Exception as e:
        import sys, traceback
        print("[ERROR] Dashboard Exception:", str(e), file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return render_template('error.html', error_code=500, error_message=f'Error al cargar dashboard: {str(e)}'), 500
