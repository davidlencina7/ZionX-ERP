
"""
Blueprint de Ventas - Registro de ventas de productos
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from datetime import datetime

from backend.services.ventas_service import VentasService
from backend.services.productos_service import ProductosService
from backend.services.asientos_service import AsientosService
from backend.utils.export_excel import exportar_ventas_excel

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route('/eliminar-multiples', methods=['POST'])
@login_required
def eliminar_multiples():
    """Eliminar varias ventas seleccionadas y restaurar stock"""
    try:
        ventas_ids = request.form.getlist('ventas_ids')
        if not ventas_ids:
            flash('No se seleccionaron ventas para eliminar.', 'warning')
            return redirect(url_for('ventas.listado'))

        ventas_service = VentasService()
        eliminadas = 0
        errores = 0
        for vid in ventas_ids:
            try:
                ventas_service.eliminar_venta(int(vid))
                eliminadas += 1
            except Exception as e:
                errores += 1
        if eliminadas:
            flash(f'✅ {eliminadas} ventas eliminadas correctamente.', 'success')
        if errores:
            flash(f'❌ {errores} ventas no pudieron eliminarse.', 'danger')
        return redirect(url_for('ventas.listado'))
    except Exception as e:
        flash(f'Error al eliminar ventas: {str(e)}', 'danger')
        return redirect(url_for('ventas.listado'))


def producto_to_dict(producto):
    """Convertir objeto Producto a diccionario"""
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'stock_actual': producto.stock,
        'costo_promedio': producto.costo_unitario
    }


@ventas_bp.route('/', methods=['GET'])
@login_required
def index():
    """Vista del formulario de venta"""
    
    try:
        productos_service = ProductosService()
        productos = productos_service.obtener_todos_productos()
        productos_dict = [producto_to_dict(p) for p in productos]
        
        return render_template('venta.html', productos=productos_dict)
    
    except Exception as e:
        flash(f'Error al cargar productos: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))


@ventas_bp.route('/registrar', methods=['POST'])
@login_required
def registrar():
    """Procesar el registro de venta"""
    
    try:
        # Obtener datos del formulario
        producto_id = request.form.get('producto_id')
        cantidad = request.form.get('cantidad')
        precio_unitario = request.form.get('precio_unitario')
        forma_pago = request.form.get('forma_pago', 'efectivo')
        
        # Validar datos
        if not producto_id or not cantidad or not precio_unitario:
            flash('Todos los campos son obligatorios', 'warning')
            return redirect(url_for('ventas.index'))
        
        # Convertir tipos
        try:
            producto_id = int(producto_id)
            cantidad = int(cantidad)
            precio_unitario = float(precio_unitario)
        except ValueError:
            flash('Formato de datos inválido', 'danger')
            return redirect(url_for('ventas.index'))
        
        # Obtener nombre del producto
        productos_service = ProductosService()
        producto = productos_service.obtener_producto_por_id(producto_id)
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('ventas.index'))
        
        # Registrar venta (el servicio valida stock automáticamente)
        ventas_service = VentasService()
        exito, mensaje, ganancia = ventas_service.registrar_venta(
            nombre_producto=producto.nombre,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            forma_pago=forma_pago
        )
        
        # Registrar asiento contable automático
        if exito:
            asientos_service = AsientosService()
            asientos_service.registrar_asiento_venta_efectivo(
                producto_nombre=producto.nombre,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                costo_unitario=producto.costo_unitario
            )
        
        flash(f'Venta registrada exitosamente: {cantidad} unidades', 'success')
        return redirect(url_for('dashboard.index'))
    
    except ValueError as e:
        # Error de validación (incluye stock insuficiente)
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('ventas.index'))
    
    except Exception as e:
        flash(f'Error al registrar venta: {str(e)}', 'danger')
        return redirect(url_for('ventas.index'))


@ventas_bp.route('/listado')
@login_required
def listado():
    """Listado de todas las ventas con opción de editar/eliminar"""
    
    try:
        ventas_service = VentasService()
        fecha_filtro = request.args.get('fecha', '')
        
        # Obtener ventas
        if fecha_filtro:
            ventas_raw = ventas_service.obtener_ventas_por_fecha(fecha_filtro)
            ventas = [
                {
                    'id': v.id,
                    'fecha': v.fecha,
                    'producto_nombre': v.producto_nombre,
                    'cantidad': v.cantidad,
                    'precio_unitario': v.precio_unitario,
                    'costo_unitario': v.costo_unitario,
                    'ganancia_unitaria': v.ganancia_unitaria
                }
                for v in ventas_raw
            ]
        else:
            ventas = ventas_service.obtener_todas_ventas()
        
        # Calcular totales
        total_ingresos = sum(v['precio_unitario'] * v['cantidad'] for v in ventas)
        total_ganancia = sum(v['ganancia_unitaria'] * v['cantidad'] for v in ventas)
        
        return render_template('ventas/listado.html', 
                             ventas=ventas,
                             fecha_filtro=fecha_filtro,
                             total_ingresos=total_ingresos,
                             total_ganancia=total_ganancia)
    
    except Exception as e:
        flash(f'Error al cargar ventas: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))


@ventas_bp.route('/editar/<int:venta_id>', methods=['GET', 'POST'])
@login_required
def editar(venta_id):
    """Editar una venta existente"""
    
    ventas_service = VentasService()
    productos_service = ProductosService()
    
    if request.method == 'POST':
        try:
            cantidad = float(request.form.get('cantidad'))
            precio_unitario = float(request.form.get('precio_unitario'))
            fecha_str = request.form.get('fecha')
            
            # Convertir fecha de datetime-local a formato BD
            if fecha_str:
                fecha_convertida = fecha_str.replace('T', ' ') + ':00'
            else:
                fecha_convertida = None
            
            # Editar venta
            ventas_service.editar_venta(
                venta_id=venta_id,
                cantidad=int(cantidad),
                precio_unitario=precio_unitario,
                fecha=fecha_convertida
            )
            
            flash('✅ Venta actualizada correctamente', 'success')
            return redirect(url_for('ventas.listado'))
        
        except Exception as e:
            flash(f'Error al editar venta: {str(e)}', 'danger')
            return redirect(url_for('ventas.editar', venta_id=venta_id))
    
    # GET - Mostrar formulario
    try:
        venta = ventas_service.obtener_venta_por_id(venta_id)
        
        if not venta:
            flash('Venta no encontrada', 'danger')
            return redirect(url_for('ventas.listado'))
        
        producto = productos_service.obtener_producto_por_id(venta.producto_id)
        
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('ventas.listado'))
        
        # Convertir venta a diccionario
        venta_dict = {
            'id': venta.id,
            'producto_id': venta.producto_id,
            'cantidad': venta.cantidad,
            'precio_unitario': venta.precio_unitario,
            'costo_unitario': venta.costo_unitario,
            'ganancia_unitaria': venta.ganancia_unitaria,
            'fecha': venta.fecha
        }
        
        producto_dict = {
            'id': producto.id,
            'nombre': producto.nombre,
            'stock': producto.stock
        }
        
        return render_template('ventas/editar.html', 
                             venta=venta_dict,
                             producto=producto_dict)
    
    except Exception as e:
        flash(f'Error al cargar venta: {str(e)}', 'danger')
        return redirect(url_for('ventas.listado'))


@ventas_bp.route('/eliminar/<int:venta_id>', methods=['POST'])
@login_required
def eliminar(venta_id):
    """Eliminar una venta y restaurar el stock"""
    
    try:
        ventas_service = VentasService()
        ventas_service.eliminar_venta(venta_id)
        flash('✅ Venta eliminada correctamente. Stock restaurado.', 'success')
    
    except Exception as e:
        flash(f'Error al eliminar venta: {str(e)}', 'danger')
    
    return redirect(url_for('ventas.listado'))


@ventas_bp.route('/exportar', methods=['GET'])
@login_required
def exportar():
    """Exportar ventas a Excel"""
    try:
        ventas_service = VentasService()
        
        # Obtener todas las ventas
        ventas = ventas_service.obtener_todas_ventas()
        
        # Convertir a diccionarios
        ventas_dict = []
        for venta in ventas:
            ventas_dict.append({
                'id': venta.id,
                'fecha': venta.fecha.strftime('%Y-%m-%d %H:%M'),
                'producto_nombre': venta.producto.nombre if venta.producto else 'Desconocido',
                'cantidad': venta.cantidad,
                'precio_unitario': venta.precio_unitario,
                'ganancia_unitaria': venta.ganancia_unitaria
            })
        
        # Generar Excel
        excel_file = exportar_ventas_excel(ventas_dict)
        
        # Nombre del archivo
        filename = f"ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'danger')
        return redirect(url_for('ventas.listado'))

    return redirect(url_for('ventas.listado'))
