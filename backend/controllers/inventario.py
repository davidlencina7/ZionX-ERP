"""
Blueprint de Inventario - Visualización de productos
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required
from datetime import datetime

from backend.services.productos_service import ProductosService
from backend.utils.export_excel import exportar_inventario_excel

inventario_bp = Blueprint('inventario', __name__)


def producto_to_dict(producto):
    """Convertir objeto Producto a diccionario"""
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'stock_actual': producto.stock,
        'stock_minimo': 5,  # Valor por defecto
        'costo_promedio': producto.costo_unitario,
        'margen_venta': producto.margen_porcentaje
    }


@inventario_bp.route('/')
@login_required
def index():
    """Vista de tabla de inventario"""
    
    try:
        productos_service = ProductosService()
        productos = productos_service.obtener_todos_productos()
        productos_dict = [producto_to_dict(p) for p in productos]
        
        # Calcular métricas
        total_productos = len(productos_dict)
        stock_total = sum(p['stock_actual'] for p in productos_dict)
        valor_inventario = sum(p['stock_actual'] * p['costo_promedio'] for p in productos_dict)
        
        metricas = {
            'total_productos': total_productos,
            'stock_total': stock_total,
            'valor_inventario': valor_inventario
        }
        
        return render_template('inventario.html', productos=productos_dict, metricas=metricas)
    
    except Exception as e:
        flash(f'Error al cargar inventario: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))


@inventario_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_producto():
    """Crear un nuevo producto"""
    
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre', '').strip()
            stock = int(request.form.get('stock_inicial', 0))
            costo_unitario = float(request.form.get('costo_unitario', 0))
            # margen_porcentaje y precio_sugerido no se usan en crear_producto

            if not nombre:
                flash('El nombre del producto es obligatorio', 'warning')
                return redirect(url_for('inventario.crear_producto'))

            productos_service = ProductosService()
            productos_service.crear_producto(
                nombre=nombre,
                stock=stock,
                costo_unitario=costo_unitario
            )

            flash(f'✅ Producto "{nombre}" creado correctamente', 'success')
            return redirect(url_for('inventario.index'))

        except Exception as e:
            flash(f'Error al crear producto: {str(e)}', 'danger')
            return redirect(url_for('inventario.crear_producto'))
    
    # GET - Mostrar formulario
    return render_template('productos/crear.html')


@inventario_bp.route('/editar/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    """Editar un producto existente"""
    
    productos_service = ProductosService()
    
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre', '').strip()
            stock = int(request.form.get('stock', 0))
            costo_unitario = float(request.form.get('costo_unitario', 0))
            margen_porcentaje = float(request.form.get('margen_porcentaje', 0))
            
            if not nombre:
                flash('El nombre del producto es obligatorio', 'warning')
                return redirect(url_for('inventario.editar_producto', producto_id=producto_id))
            
            # Calcular precio sugerido
            precio_sugerido = costo_unitario * (1 + margen_porcentaje / 100)
            
            # Actualizar producto
            productos_service.actualizar_producto(
                producto_id=producto_id,
                nombre=nombre,
                stock=stock,
                costo_unitario=costo_unitario,
                margen_porcentaje=margen_porcentaje,
                precio_sugerido=precio_sugerido
            )
            
            flash(f'✅ Producto "{nombre}" actualizado correctamente', 'success')
            return redirect(url_for('inventario.index'))
        
        except Exception as e:
            flash(f'Error al actualizar producto: {str(e)}', 'danger')
            return redirect(url_for('inventario.editar_producto', producto_id=producto_id))
    
    # GET - Mostrar formulario
    try:
        producto = productos_service.obtener_producto_por_id(producto_id)
        
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('inventario.index'))
        
        producto_dict = {
            'id': producto.id,
            'nombre': producto.nombre,
            'stock': producto.stock,
            'costo_unitario': producto.costo_unitario,
            'margen_porcentaje': producto.margen_porcentaje
        }
        
        return render_template('productos/editar.html', producto=producto_dict)
    
    except Exception as e:
        flash(
            f"[ERROR] 🔴 Error al cargar producto en Inventario de Productos - ZionX ERP: {str(e)}\n"
            f"SUGERENCIA: Revise la consulta SQL y los datos enviados. Verifique que el parámetro 'id' esté correctamente definido y que la sintaxis del WHERE sea válida.\n",
            'danger'
        )
        return redirect(url_for('inventario.index'))


@inventario_bp.route('/detalle/<int:producto_id>')
@login_required
def detalle_producto(producto_id):
    """Ver detalles de un producto"""
    
    try:
        productos_service = ProductosService()
        producto = productos_service.obtener_producto_por_id(producto_id)
        
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('inventario.index'))
        
        # Obtener estadísticas del producto
        from backend.services.ventas_service import VentasService
        from backend.services.compras_service import ComprasService
        
        ventas_service = VentasService()
        compras_service = ComprasService()
        
        historial_ventas = ventas_service.obtener_historial_ventas(producto.nombre)
        historial_compras = compras_service.obtener_historial_compras(producto.nombre)
        
        stats = {
            'total_ventas': len(historial_ventas),
            'unidades_vendidas': sum(v['cantidad'] for v in historial_ventas),
            'total_compras': len(historial_compras),
            'unidades_compradas': sum(c['cantidad'] for c in historial_compras)
        }
        
        producto_dict = {
            'id': producto.id,
            'nombre': producto.nombre,
            'stock': producto.stock,
            'costo_unitario': producto.costo_unitario,
            'margen_porcentaje': producto.margen_porcentaje
        }
        
        return render_template('productos/detalle.html', 
                             producto=producto_dict,
                             stats=stats)
    
    except Exception as e:
        flash(f'Error al cargar detalle: {str(e)}', 'danger')
        return redirect(url_for('inventario.index'))


@inventario_bp.route('/eliminar/<int:producto_id>', methods=['POST'])
@login_required
def eliminar_producto(producto_id):
    """Eliminar un producto (solo si no tiene transacciones)"""
    
    try:
        productos_service = ProductosService()
        exito, mensaje = productos_service.eliminar_producto(producto_id)
        
        if exito:
            flash(f'✅ {mensaje}', 'success')
        else:
            flash(f'❌ {mensaje}', 'danger')
    
    except Exception as e:
        flash(f'Error al eliminar producto: {str(e)}', 'danger')
    
    return redirect(url_for('inventario.index'))


@inventario_bp.route('/exportar', methods=['GET'])
@login_required
def exportar():
    """Exportar inventario a Excel"""
    try:
        productos_service = ProductosService()
        
        # Obtener todos los productos
        productos = productos_service.obtener_todos_productos()
        
        # Convertir a diccionarios
        productos_dict = []
        for producto in productos:
            productos_dict.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'stock_actual': producto.stock,
                'costo_promedio': producto.costo_unitario,
                'margen_venta': producto.margen_porcentaje
            })
        
        # Generar Excel
        excel_file = exportar_inventario_excel(productos_dict)
        
        # Nombre del archivo
        filename = f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'danger')
        return redirect(url_for('inventario.index'))

