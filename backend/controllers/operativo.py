"""
Rutas del módulo operativo simplificado
Interfaz ultra simple para uso diario
"""
import logging
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from backend.services.ventas_service import VentasService
from backend.services.compras_service import ComprasService
from backend.services.productos_service import ProductosService
from backend.services.asientos_service import AsientosService
from backend.utils.exceptions import (
    ProductoNoEncontradoError,
    StockInsuficienteError,
    ErrorValidacionError
)

logger = logging.getLogger(__name__)

operativo_bp = Blueprint('operativo', __name__, url_prefix='/operativo')

@operativo_bp.route('/')
@login_required
def index():
    """Pantalla principal con 4 botones grandes"""
    try:
        productos_service = ProductosService()
        ventas_service = VentasService()
        compras_service = ComprasService()
        
        # Obtener datos del día
        hoy = date.today().strftime('%Y-%m-%d')
        
        # Ventas del día
        ventas_hoy = ventas_service.obtener_ventas_por_fecha(hoy)
        total_ventas_hoy = sum([v.precio_unitario * v.cantidad for v in ventas_hoy])
        
        # Compras del día
        compras_hoy = compras_service.obtener_compras_por_fecha(hoy)
        total_compras_hoy = sum([c.costo_unitario * c.cantidad for c in compras_hoy])
        
        # Caja del día
        caja_hoy = total_ventas_hoy - total_compras_hoy
        
        # Productos con stock bajo
        productos = productos_service.listar_productos()
        productos_bajo_stock = sum(1 for p in productos if p.stock <= p.stock_minimo)
        
        # Últimas operaciones
        ultimas_operaciones = []
        
        # Agregar ventas
        for v in ventas_hoy[-5:]:
            produto = productos_service.obtener_producto_por_id(v.producto_id)
            
            # Extraer hora de la fecha
            if hasattr(v.fecha, 'strftime'):
                hora = v.fecha.strftime('%H:%M')
            elif isinstance(v.fecha, str):
                # Si es string tipo '2026-02-11 18:50:57', extraer hora
                hora = v.fecha[11:16] if len(v.fecha) >= 16 else ''
            else:
                hora = ''
            
            ultimas_operaciones.append({
                'id': v.id,
                'hora': hora,
                'tipo': 'venta',
                'producto': produto.nombre if produto else 'Desconocido',
                'cantidad': v.cantidad,
                'monto': v.precio_unitario * v.cantidad
            })
        
        # Agregar compras
        for c in compras_hoy[-5:]:
            produto = productos_service.obtener_producto_por_id(c.producto_id)
            
            # Extraer hora de la fecha
            if hasattr(c.fecha, 'strftime'):
                hora = c.fecha.strftime('%H:%M')
            elif isinstance(c.fecha, str):
                # Si es string tipo '2026-02-11 18:50:57', extraer hora
                hora = c.fecha[11:16] if len(c.fecha) >= 16 else ''
            else:
                hora = ''
            
            ultimas_operaciones.append({
                'id': c.id,
                'hora': hora,
                'tipo': 'compra',
                'producto': produto.nombre if produto else 'Desconocido',
                'cantidad': c.cantidad,
                'monto': c.costo_unitario * c.cantidad
            })
        
        # Ordenar por hora descendente
        ultimas_operaciones.sort(key=lambda x: x['hora'], reverse=True)
        ultimas_operaciones = ultimas_operaciones[:10]
        
        return render_template('operativo.html',
                             caja_hoy=caja_hoy,
                             ventas_hoy=len(ventas_hoy),
                             balance_hoy=caja_hoy,
                             productos_bajo_stock=productos_bajo_stock,
                             ultimas_operaciones=ultimas_operaciones)
    
    except Exception as e:
        logger.error(f"Error en pantalla operativa: {str(e)}")
        flash(f"Error al cargar datos: {str(e)}", "error")
        return render_template('operativo.html',
                             caja_hoy=0,
                             ventas_hoy=0,
                             balance_hoy=0,
                             productos_bajo_stock=0,
                             ultimas_operaciones=[])


@operativo_bp.route('/venta', methods=['GET', 'POST'])
@login_required
def nueva_venta():
    """Flujo simplificado de venta"""
    productos_service = ProductosService()
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre_producto = request.form.get('producto')
            monto = float(request.form.get('monto'))  # Total a cobrar al cliente
            cantidad = float(request.form.get('cantidad'))  # kg o unidades vendidas
            # Capturar forma de pago desde el formulario
            forma_pago = request.form.get('forma_pago', 'efectivo')
            unidades_inventario = request.form.get('unidades_inventario')  # Unidades físicas para inventario
            
            # Si viene unidades_inventario, es una venta por kg, sino es por unidades
            cantidad_inventario = float(unidades_inventario) if unidades_inventario else cantidad
            
            # Validaciones básicas
            if not nombre_producto or cantidad <= 0 or monto <= 0:
                flash('Datos inválidos', 'error')
                return redirect(url_for('operativo.nueva_venta'))
            
            # Obtener producto para validar stock y obtener costo
            producto = productos_service.obtener_producto_por_nombre(nombre_producto)
            if not producto:
                flash(f'Producto "{nombre_producto}" no encontrado', 'error')
                return redirect(url_for('operativo.nueva_venta'))
            
            # Validar stock usando la cantidad de inventario (unidades físicas)
            if cantidad_inventario > producto.stock:
                flash(f'Stock insuficiente. Disponible: {producto.stock} unidades', 'error')
                return redirect(url_for('operativo.nueva_venta'))
            
            # Calcular precio_unitario desde el monto que ingresó el usuario
            # Esto permite vender a cualquier precio, no solo el precio sugerido
            precio_unitario = monto / cantidad
            
            # Registrar venta
            ventas_service = VentasService()
            
            exito, mensaje, ganancia = ventas_service.registrar_venta(
                nombre_producto=nombre_producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                cantidad_inventario=cantidad_inventario,
                forma_pago=forma_pago
            )
            
            if exito:
                # Registrar asiento contable automático
                asientos_service = AsientosService()
                asientos_service.registrar_asiento_venta_efectivo(
                    producto_nombre=nombre_producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    costo_unitario=producto.costo_unitario
                )
                flash(f'✅ Venta registrada! Ganancia: ${ganancia:.2f}', 'success')
                logger.info(f"Venta registrada: {nombre_producto} x{cantidad} [{forma_pago}]")
                return redirect(url_for('operativo.index'))
            else:
                flash(mensaje, 'error')
                return redirect(url_for('operativo.nueva_venta'))
        
        except StockInsuficienteError as e:
            flash(str(e), 'error')
            return redirect(url_for('operativo.nueva_venta'))
        
        except Exception as e:
            logger.error(f"Error al registrar venta: {str(e)}")
            flash(f'Error al registrar venta: {str(e)}', 'error')
            return redirect(url_for('operativo.nueva_venta'))
    
    # GET - Mostrar formulario
    try:
        # Obtener datos de productos principales
        productos_dict = {}
        nombres_productos = ['pollo entero', 'pata muslo', 'maple huevo', 'huevo unidad']
        
        for nombre in nombres_productos:
            try:
                producto = productos_service.obtener_producto_por_nombre(nombre)
                if producto:
                    # Usar precio_sugerido (atributo correcto del modelo Producto)
                    precio = producto.precio_sugerido if producto.precio_sugerido > 0 else producto.costo_unitario * 1.3
                    productos_dict[nombre] = {
                        'stock': producto.stock,
                        'precio': precio
                    }
                else:
                    productos_dict[nombre] = {'stock': 0, 'precio': 0}
            except Exception as e:
                logger.error(f"Error al cargar producto {nombre}: {str(e)}")
                productos_dict[nombre] = {'stock': 0, 'precio': 0}
        
        return render_template('operativo_venta.html', productos=productos_dict)
    
    except Exception as e:
        logger.error(f"Error al cargar formulario de venta: {str(e)}")
        flash(f"Error al cargar formulario: {str(e)}", "error")
        return redirect(url_for('operativo.index'))


@operativo_bp.route('/compra', methods=['GET', 'POST'])
@login_required
def nueva_compra():
    """Flujo simplificado de compra"""
    productos_service = ProductosService()
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre_producto = request.form.get('producto')
            cantidad = float(request.form.get('cantidad'))
            costo_total = float(request.form.get('costo_total'))
            proveedor = request.form.get('proveedor')
            
            # Validaciones básicas
            if not nombre_producto or cantidad <= 0 or costo_total < 0:
                flash('Datos inválidos', 'error')
                return redirect(url_for('operativo.nueva_compra'))
            
            # Calcular costo unitario
            costo_unitario = costo_total / cantidad
            
            # Registrar compra
            compras_service = ComprasService()
            exito, mensaje = compras_service.registrar_compra(
                nombre_producto=nombre_producto,
                cantidad=cantidad,
                costo_unitario=costo_unitario
            )
            
            if exito:
                # Registrar asiento contable automático
                asientos_service = AsientosService()
                asientos_service.registrar_asiento_compra_contado(
                    producto_nombre=nombre_producto,
                    cantidad=cantidad,
                    costo_unitario=costo_unitario,
                    proveedor=proveedor
                )
                
                flash(f'✅ Compra registrada! {mensaje}', 'success')
                logger.info(f"Compra registrada: {nombre_producto} x{cantidad} de {proveedor}")
                return redirect(url_for('operativo.index'))
            else:
                flash(mensaje, 'error')
                return redirect(url_for('operativo.nueva_compra'))
        
        except Exception as e:
            logger.error(f"Error al registrar compra: {str(e)}")
            flash(f'Error al registrar compra: {str(e)}', 'error')
            return redirect(url_for('operativo.nueva_compra'))
    
    # GET - Mostrar formulario
    try:
        # Obtener datos de productos principales
        productos_dict = {}
        nombres_productos = ['pollo entero', 'pata muslo', 'maple huevo', 'huevo unidad']
        
        for nombre in nombres_productos:
            try:
                producto = productos_service.obtener_producto_por_nombre(nombre)
                if producto:
                    productos_dict[nombre] = {'stock': producto.stock}
                else:
                    productos_dict[nombre] = {'stock': 0}
            except:
                productos_dict[nombre] = {'stock': 0}
        
        return render_template('operativo_compra.html', productos=productos_dict)
    
    except Exception as e:
        logger.error(f"Error al cargar formulario de compra: {str(e)}")
        flash(f"Error al cargar formulario: {str(e)}", "error")
        return redirect(url_for('operativo.index'))


@operativo_bp.route('/venta/eliminar/<int:venta_id>', methods=['POST'])
@login_required
def eliminar_venta(venta_id):
    """Eliminar una venta y restaurar el stock"""
    try:
        ventas_service = VentasService()
        ventas_service.eliminar_venta(venta_id)
        flash('✅ Venta eliminada correctamente', 'success')
        logger.info(f"Venta {venta_id} eliminada por usuario")
    except Exception as e:
        logger.error(f"Error al eliminar venta {venta_id}: {str(e)}")
        flash(
            f"[ERROR] 🔴 Error al eliminar venta en Operativo - ZionX ERP: {str(e)}\n"
            f"SUGERENCIA: Revise la consulta SQL y asegúrese de que el parámetro 'id' esté correctamente definido. Verifique la sintaxis del WHERE y que la venta exista.\n",
            'error'
        )
    
    return redirect(url_for('operativo.index'))


@operativo_bp.route('/compra/eliminar/<int:compra_id>', methods=['POST'])
@login_required
def eliminar_compra(compra_id):
    """Eliminar una compra y ajustar el stock"""
    try:
        compras_service = ComprasService()
        exito, mensaje = compras_service.eliminar_compra(compra_id)
        
        if exito:
            if mensaje:
                # Hay advertencia (stock negativo)
                flash(f'Compra eliminada. {mensaje}', 'warning')
            else:
                flash('✅ Compra eliminada correctamente', 'success')
            logger.info(f"Compra {compra_id} eliminada por usuario")
        
    except Exception as e:
        logger.error(f"Error al eliminar compra {compra_id}: {str(e)}")
        flash(f'Error al eliminar compra: {str(e)}', 'error')
    
    return redirect(url_for('operativo.index'))


@operativo_bp.route('/venta/editar/<int:venta_id>', methods=['GET', 'POST'])
@login_required
def editar_venta(venta_id):
    """Editar una venta existente"""
    ventas_service = VentasService()
    productos_service = ProductosService()
    
    if request.method == 'POST':
        try:
            cantidad = float(request.form.get('cantidad'))
            precio_unitario = float(request.form.get('precio_unitario'))
            fecha_str = request.form.get('fecha')
            
            # Convertir fecha de formato datetime-local a formato de base de datos
            fecha = None
            if fecha_str:
                # datetime-local viene como "2026-02-12T03:33", convertir a "2026-02-12 03:33:00"
                fecha = fecha_str.replace('T', ' ') + ':00'
            
            ventas_service.editar_venta(venta_id, cantidad, precio_unitario, fecha)
            flash('✅ Venta actualizada correctamente', 'success')
            logger.info(f"Venta {venta_id} editada: cantidad={cantidad}, precio={precio_unitario}, fecha={fecha}")
            return redirect(url_for('operativo.index'))
        
        except Exception as e:
            logger.error(f"Error al editar venta {venta_id}: {str(e)}")
            flash(f'Error al editar venta: {str(e)}', 'error')
            return redirect(url_for('operativo.editar_venta', venta_id=venta_id))
    
    # GET - Mostrar formulario de edición
    try:
        venta = ventas_service.obtener_venta_por_id(venta_id)
        if not venta:
            flash('Venta no encontrada', 'error')
            return redirect(url_for('operativo.index'))
        
        producto = productos_service.obtener_producto_por_id(venta.producto_id)
        
        return render_template('operativo_editar_venta.html', venta=venta, producto=producto)
    
    except Exception as e:
        logger.error(f"Error al cargar venta {venta_id}: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('operativo.index'))


@operativo_bp.route('/compra/editar/<int:compra_id>', methods=['GET', 'POST'])
@login_required
def editar_compra(compra_id):
    """Editar una compra existente"""
    compras_service = ComprasService()
    productos_service = ProductosService()
    
    if request.method == 'POST':
        try:
            cantidad = float(request.form.get('cantidad'))
            costo_unitario = float(request.form.get('costo_unitario'))
            fecha_str = request.form.get('fecha')
            
            # Convertir fecha de formato datetime-local a formato de base de datos
            fecha = None
            if fecha_str:
                # datetime-local viene como "2026-02-12T03:27", convertir a "2026-02-12 03:27:00"
                fecha = fecha_str.replace('T', ' ') + ':00'
            
            compras_service.editar_compra(compra_id, cantidad, costo_unitario, fecha)
            flash('✅ Compra actualizada correctamente', 'success')
            logger.info(f"Compra {compra_id} editada: cantidad={cantidad}, costo={costo_unitario}, fecha={fecha}")
            return redirect(url_for('operativo.index'))
        
        except Exception as e:
            logger.error(f"Error al editar compra {compra_id}: {str(e)}")
            flash(f'Error al editar compra: {str(e)}', 'error')
            return redirect(url_for('operativo.editar_compra', compra_id=compra_id))
    
    # GET - Mostrar formulario de edición
    try:
        compra = compras_service.obtener_compra_por_id(compra_id)
        if not compra:
            flash('Compra no encontrada', 'error')
            return redirect(url_for('operativo.index'))
        
        producto = productos_service.obtener_producto_por_id(compra.producto_id)
        
        return render_template('operativo_editar_compra.html', compra=compra, producto=producto)
    
    except Exception as e:
        logger.error(f"Error al cargar compra {compra_id}: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('operativo.index'))

