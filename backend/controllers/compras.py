"""
Blueprint de Compras - Registro de compras de productos
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from datetime import datetime

from backend.services.compras_service import ComprasService
from backend.services.productos_service import ProductosService
from backend.services.asientos_service import AsientosService
from backend.utils.export_excel import exportar_compras_excel

compras_bp = Blueprint('compras', __name__)


def producto_to_dict(producto):
    """Convertir objeto Producto a diccionario"""
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'stock_actual': producto.stock,
        'costo_promedio': producto.costo_unitario
    }


@compras_bp.route('/', methods=['GET'])
@login_required
def index():
    """Vista del formulario de compra"""
    
    try:
        productos_service = ProductosService()
        productos = productos_service.obtener_todos_productos()
        productos_dict = [producto_to_dict(p) for p in productos]
        
        return render_template('compra.html', productos=productos_dict)
    
    except Exception as e:
        flash(f'Error al cargar productos: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))


@compras_bp.route('/registrar', methods=['POST'])
@login_required
def registrar():
    """Procesar el registro de compra"""
    
    try:
        # Obtener datos del formulario
        producto_id = request.form.get('producto_id')
        cantidad = request.form.get('cantidad')
        costo_unitario = request.form.get('costo_unitario')
        
        # Validar datos
        if not producto_id or not cantidad or not costo_unitario:
            flash('Todos los campos son obligatorios', 'warning')
            return redirect(url_for('compras.index'))
        
        # Convertir tipos
        try:
            producto_id = int(producto_id)
            cantidad = int(cantidad)
            costo_unitario = float(costo_unitario)
        except ValueError:
            flash('Formato de datos inválido', 'danger')
            return redirect(url_for('compras.index'))
        
        # Obtener nombre del producto
        productos_service = ProductosService()
        producto = productos_service.obtener_producto_por_id(producto_id)
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('compras.index'))
        
        # Registrar compra
        compras_service = ComprasService()
        exito, mensaje = compras_service.registrar_compra(
            nombre_producto=producto.nombre,
            cantidad=cantidad,
            costo_unitario=costo_unitario
        )
        
        # Registrar asiento contable automático
        if exito:
            asientos_service = AsientosService()
            asientos_service.registrar_asiento_compra_contado(
                producto_nombre=producto.nombre,
                cantidad=cantidad,
                costo_unitario=costo_unitario,
                proveedor="Genérico"
            )
        
        flash(f'Compra registrada exitosamente: {cantidad} unidades', 'success')
        return redirect(url_for('dashboard.index'))
    
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'danger')
        return redirect(url_for('compras.index'))
    
    except Exception as e:
        flash(f'Error al registrar compra: {str(e)}', 'danger')
        return redirect(url_for('compras.index'))


@compras_bp.route('/listado')
@login_required
def listado():
    """Listado de todas las compras con opción de editar/eliminar"""
    
    try:
        compras_service = ComprasService()
        productos_service = ProductosService()
        fecha_filtro = request.args.get('fecha', '')
        
        # Obtener compras
        if fecha_filtro:
            compras_raw = compras_service.obtener_compras_por_fecha(fecha_filtro)
        else:
            compras_raw = compras_service.listar_compras()
        
        # Convertir a diccionarios con nombre de producto
        compras = []
        for compra in compras_raw:
            producto = productos_service.obtener_producto_por_id(compra.producto_id)
            compras.append({
                'id': compra.id,
                'fecha': compra.fecha,
                'producto_nombre': producto.nombre if producto else 'Desconocido',
                'cantidad': compra.cantidad,
                'costo_unitario': compra.costo_unitario
            })
        
        # Calcular totales
        total_unidades = sum(c['cantidad'] for c in compras)
        total_costo = sum(c['costo_unitario'] * c['cantidad'] for c in compras)
        
        return render_template('compras/listado.html', 
                             compras=compras,
                             fecha_filtro=fecha_filtro,
                             total_unidades=total_unidades,
                             total_costo=total_costo)
    
    except Exception as e:
        flash(f'Error al cargar compras: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))


@compras_bp.route('/editar/<int:compra_id>', methods=['GET', 'POST'])
@login_required
def editar(compra_id):
    """Editar una compra existente"""
    
    compras_service = ComprasService()
    productos_service = ProductosService()
    
    if request.method == 'POST':
        try:
            cantidad = float(request.form.get('cantidad'))
            costo_unitario = float(request.form.get('costo_unitario'))
            fecha_str = request.form.get('fecha')
            
            # Convertir fecha de datetime-local a formato BD
            if fecha_str:
                fecha_convertida = fecha_str.replace('T', ' ') + ':00'
            else:
                fecha_convertida = None
            
            # Editar compra
            compras_service.editar_compra(
                compra_id=compra_id,
                cantidad=int(cantidad),
                costo_unitario=costo_unitario,
                fecha=fecha_convertida
            )
            
            flash('✅ Compra actualizada correctamente', 'success')
            return redirect(url_for('compras.listado'))
        
        except Exception as e:
            flash(f'Error al editar compra: {str(e)}', 'danger')
            return redirect(url_for('compras.editar', compra_id=compra_id))
    
    # GET - Mostrar formulario
    try:
        compra = compras_service.obtener_compra_por_id(compra_id)
        
        if not compra:
            flash('Compra no encontrada', 'danger')
            return redirect(url_for('compras.listado'))
        
        producto = productos_service.obtener_producto_por_id(compra.producto_id)
        
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('compras.listado'))
        
        # Convertir compra a diccionario
        compra_dict = {
            'id': compra.id,
            'producto_id': compra.producto_id,
            'cantidad': compra.cantidad,
            'costo_unitario': compra.costo_unitario,
            'fecha': compra.fecha
        }
        
        producto_dict = {
            'id': producto.id,
            'nombre': producto.nombre,
            'stock': producto.stock
        }
        
        return render_template('compras/editar.html', 
                             compra=compra_dict,
                             producto=producto_dict)
    
    except Exception as e:
        flash(f'Error al cargar compra: {str(e)}', 'danger')
        return redirect(url_for('compras.listado'))



@compras_bp.route('/eliminar/<int:compra_id>', methods=['POST'])
@login_required
def eliminar(compra_id):
    """Eliminar una compra y ajustar el stock"""
    try:
        compras_service = ComprasService()
        exito, mensaje = compras_service.eliminar_compra(compra_id)
        if exito:
            if mensaje:
                flash(f'Compra eliminada. {mensaje}', 'warning')
            else:
                flash('✅ Compra eliminada correctamente. Stock ajustado.', 'success')
        else:
            flash('Error al eliminar compra', 'danger')
    except Exception as e:
        flash(f'Error al eliminar compra: {str(e)}', 'danger')
    return redirect(url_for('compras.listado'))


# NUEVO: Eliminación múltiple de compras
@compras_bp.route('/eliminar-multiples', methods=['POST'])
@login_required
def eliminar_multiples():
    """Eliminar varias compras seleccionadas y ajustar stock"""
    try:
        compras_ids = request.form.getlist('compras_ids')
        if not compras_ids:
            flash('No se seleccionaron compras para eliminar.', 'warning')
            return redirect(url_for('compras.listado'))

        compras_service = ComprasService()
        exitos = 0
        advertencias = []
        errores = 0
        for cid in compras_ids:
            try:
                exito, mensaje = compras_service.eliminar_compra(int(cid))
                if exito:
                    exitos += 1
                    if mensaje:
                        advertencias.append(mensaje)
                else:
                    errores += 1
            except Exception as e:
                errores += 1
                advertencias.append(f"ID {cid}: {str(e)}")

        if exitos:
            flash(f'✅ {exitos} compras eliminadas correctamente.', 'success')
        if advertencias:
            flash(' '.join(advertencias), 'warning')
        if errores:
            flash(f'❌ {errores} compras no se pudieron eliminar.', 'danger')
    except Exception as e:
        flash(f'Error al eliminar compras: {str(e)}', 'danger')
    return redirect(url_for('compras.listado'))


@compras_bp.route('/exportar', methods=['GET'])
@login_required
def exportar():
    """Exportar compras a Excel"""
    try:
        compras_service = ComprasService()
        
        # Obtener todas las compras
        compras = compras_service.obtener_todas_compras()
        
        # Convertir a diccionarios
        compras_dict = []
        for compra in compras:
            compras_dict.append({
                'id': compra.id,
                'fecha': compra.fecha.strftime('%Y-%m-%d %H:%M'),
                'producto_nombre': compra.producto.nombre if compra.producto else 'Desconocido',
                'cantidad': compra.cantidad,
                'costo_unitario': compra.costo_unitario
            })
        
        # Generar Excel
        excel_file = exportar_compras_excel(compras_dict)
        
        # Nombre del archivo
        filename = f"compras_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'danger')
        return redirect(url_for('compras.listado'))

    return redirect(url_for('compras.listado'))
