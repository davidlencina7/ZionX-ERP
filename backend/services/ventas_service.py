"""
Servicio de gestión de ventas
Lógica de negocio para ventas y ganancias
"""
import logging
from datetime import datetime
from typing import Optional, Tuple, List

from backend.database.connection import DatabaseConnection
from backend.models.venta import Venta
from backend.utils.exceptions import (
    ProductoNoEncontradoError,
    StockInsuficienteError,
    ErrorTransaccionError,
    ErrorValidacionError,
)

logger = logging.getLogger(__name__)

# Constante para relación maple huevo - huevo unidad
HUEVOS_POR_MAPLE = 30


class VentasService:
    """Servicio para gestionar ventas de productos"""
    
    def __init__(self) -> None:
        self.db = DatabaseConnection.get_instance()
        logger.debug("VentasService inicializado")
    
    def registrar_venta(
        self,
        nombre_producto: str,
        cantidad: float,
        precio_unitario: float,
        cantidad_inventario: float = None,
        forma_pago: str = 'efectivo'
    ) -> Tuple[bool, str, float]:
        """
        Registrar una venta de producto
        Actualiza el stock, registra la venta y calcula ganancia
        
                    cursor.execute(
                        'SELECT id, stock, costo_unitario FROM productos WHERE nombre = %s',
                        (nombre_producto,)
                    )
            cantidad_inventario: Unidades físicas a descontar del inventario (opcional)
                                Si no se provee, se usa la cantidad
        
        Returns:
            Tuple[bool, str, float]: (éxito, mensaje, ganancia_total)
        
        Raises:
            ErrorValidacionError: Si datos son inválidos
            ProductoNoEncontradoError: Si el producto no existe
            StockInsuficienteError: Si no hay stock suficiente
        """
        # Si no se especifica cantidad_inventario, usar la cantidad
        if cantidad_inventario is None:
            cantidad_inventario = cantidad
        # Validar entrada
        if cantidad <= 0:
            raise ErrorValidacionError("cantidad", cantidad, "Debe ser mayor a 0")
        
        if precio_unitario < 0:
            raise ErrorValidacionError("precio_unitario", precio_unitario, "No puede ser negativo")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Validar que el producto existe
            cursor.execute(
                'SELECT id, stock, costo_unitario FROM productos WHERE nombre = %s',
                (nombre_producto,)
            )
            row = cursor.fetchone()
            if not row:
                raise ProductoNoEncontradoError(nombre_producto)
            producto_id, stock, costo_unitario = row

            if cantidad_inventario > stock:
                logger.warning(
                    f"Stock insuficiente en venta: {nombre_producto} "
                    f"(solicitado: {cantidad_inventario}, disponible: {stock})"
                )
                raise StockInsuficienteError(nombre_producto, cantidad_inventario, stock)

            # Calcular ganancia unitaria y total
            ganancia_unitaria = precio_unitario - costo_unitario
            ganancia_total = ganancia_unitaria * cantidad

            # Insertar la venta
            cursor.execute(
                '''INSERT INTO ventas 
                   (producto_id, cantidad, precio_unitario, costo_unitario, ganancia_unitaria, fecha, forma_pago)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (producto_id, cantidad, precio_unitario, costo_unitario, ganancia_unitaria, datetime.now(), forma_pago)
            )

            # Actualizar stock usando cantidad_inventario (unidades físicas)
            cursor.execute(
                'UPDATE productos SET stock = stock - %s WHERE id = %s',
                (cantidad_inventario, producto_id)
            )

            # Si es maple huevo, también actualizar huevo unidad
            if nombre_producto.lower() == 'maple huevo':
                self._ajustar_huevo_unidad(cursor, -cantidad_inventario * HUEVOS_POR_MAPLE)

            conn.commit()

            mensaje = f'Venta registrada. Ganancia: ${ganancia_total:.2f}'
            logger.info(
                f"Venta registrada: {nombre_producto} x{cantidad} @ ${precio_unitario:.2f} "
                f"-> Ganancia: ${ganancia_total:.2f}"
            )
            return True, mensaje, ganancia_total

        except (ProductoNoEncontradoError, StockInsuficienteError, ErrorValidacionError) as e:
            raise ErrorTransaccionError("registrar_venta", str(e))
        finally:
            conn.close()
    
    def calcular_ganancia_total_producto(self, nombre_producto: str) -> Tuple[bool, float]:
        """
        Calcular ganancia acumulada de un producto
        
        Args:
            nombre_producto: Nombre del producto
        
        Returns:
            Tuple[bool, float]: (encontrado, ganancia_total)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                     '''SELECT COALESCE(SUM(ventas.ganancia_unitaria * ventas.cantidad), 0.0) as total_ganancia,
                                  COUNT(*) as total_ventas
                         FROM ventas
                         JOIN productos ON ventas.producto_id = productos.id
                         WHERE productos.nombre = %s''',
                     (nombre_producto,)
            )
            row = cursor.fetchone()
            if not row:
                return False, 0.0
            total_ganancia, total_ventas = row[0], row[1]
            ganancia = round(total_ganancia or 0.0, 2)
            if (total_ventas or 0) == 0:
                logger.debug(f"Ganancia de {nombre_producto}: sin ventas registradas")
                return False, 0.0
            logger.debug(f"Ganancia de {nombre_producto}: ${ganancia:.2f} (ventas: {total_ventas})")
            return True, ganancia
        finally:
            conn.close()
    
    def calcular_ganancia_total_sistema(self) -> float:
        """
        Calcular ganancia total del sistema
        
        Returns:
            Ganancia total acumulada
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT COALESCE(SUM(ganancia_unitaria * cantidad), 0.0) FROM ventas'
            )
            row = cursor.fetchone()
            ganancia = row[0] if row else 0.0
            logger.debug(f"Ganancia total del sistema: ${ganancia:.2f}")
            return round(ganancia, 2)
        finally:
            conn.close()
    
    def obtener_historial_ventas(self, nombre_producto: str) -> List[dict]:
        """
        Obtener historial de ventas de un producto
        
        Args:
            nombre_producto: Nombre del producto
        
        Returns:
            Lista de ventas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''SELECT ventas.id, ventas.cantidad, ventas.precio_unitario,
                   ventas.costo_unitario, ventas.ganancia_unitaria, ventas.fecha
                   FROM ventas
                   JOIN productos ON ventas.producto_id = productos.id
                   WHERE productos.nombre = %s
                   ORDER BY ventas.fecha DESC, ventas.id DESC''',
                (nombre_producto,)
            )
            colnames = [desc[0] for desc in cursor.description]
            ventas = [dict(zip(colnames, row)) for row in cursor.fetchall()]
            logger.debug(f"Consultado historial de {len(ventas)} ventas para {nombre_producto}")
            return ventas
        finally:
            conn.close()
    
    def obtener_todas_ventas(self) -> List[dict]:
        """
        Obtener todas las ventas del sistema
        
        Returns:
            Lista de todas las ventas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''SELECT ventas.id, productos.nombre, ventas.cantidad, 
                   ventas.precio_unitario, ventas.costo_unitario, 
                   ventas.ganancia_unitaria, ventas.fecha
                   FROM ventas
                   JOIN productos ON ventas.producto_id = productos.id
                   ORDER BY ventas.fecha DESC'''
            )
            colnames = [desc[0] for desc in cursor.description]
            ventas = [dict(zip(colnames, row)) for row in cursor.fetchall()]
            logger.debug(f"Consultadas {len(ventas)} ventas del sistema")
            return ventas
        finally:
            conn.close()
    
    def listar_ventas(self) -> List[Venta]:
        """
        Listar todas las ventas como objetos Venta
        
        Returns:
            Lista de objetos Venta
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''SELECT id, producto_id, cantidad, precio_unitario, 
                   costo_unitario, ganancia_unitaria, fecha
                   FROM ventas
                   ORDER BY fecha DESC'''
            )
            ventas = []
            for row in cursor.fetchall():
                venta = Venta(
                    id=row[0],
                    producto_id=row[1],
                    cantidad=row[2],
                    precio_unitario=row[3],
                    costo_unitario=row[4],
                    ganancia_unitaria=row[5],
                    fecha=row[6],
                    mes_contable=None
                )
                ventas.append(venta)
            logger.debug(f"Listadas {len(ventas)} ventas")
            return ventas
        finally:
            conn.close()
    
    def obtener_ventas_por_fecha(self, fecha: str) -> List[Venta]:
        """
        Obtener ventas de una fecha específica
        
        Args:
            fecha: Fecha en formato YYYY-MM-DD
        
        Returns:
            Lista de objetos Venta
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''SELECT id, producto_id, cantidad, precio_unitario, 
                   costo_unitario, ganancia_unitaria, fecha
                   FROM ventas
                   WHERE DATE(fecha) = %s
                   ORDER BY fecha DESC''',
                (fecha,)
            )
            ventas = []
            for row in cursor.fetchall():
                venta = Venta(
                    id=row[0],
                    producto_id=row[1],
                    cantidad=row[2],
                    precio_unitario=row[3],
                    costo_unitario=row[4],
                    ganancia_unitaria=row[5],
                    fecha=row[6],
                    mes_contable=None
                )
                ventas.append(venta)
            logger.debug(f"Listadas {len(ventas)} ventas para fecha {fecha}")
            return ventas
        finally:
            conn.close()
    
    def eliminar_venta(self, venta_id: int) -> bool:
        """
        Eliminar una venta y restaurar el stock
        
        Args:
            venta_id: ID de la venta a eliminar
        
        Returns:
            True si se eliminó correctamente
            
        Raises:
            ErrorTransaccionError: Si hay error en la transacción
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener datos de la venta antes de eliminar
            cursor.execute(
                'SELECT producto_id, cantidad FROM ventas WHERE id = %s',
                (venta_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"Intento de eliminar venta inexistente: ID {venta_id}")
                raise ErrorValidacionError("venta_id", venta_id, "La venta no existe")
            
            producto_id, cantidad = row[0], row[1]
            
            # Obtener nombre del producto para verificar si es maple
            cursor.execute(
                'SELECT nombre FROM productos WHERE id = %s',
                (producto_id,)
            )
            row_nombre = cursor.fetchone()
            nombre_producto = row_nombre[0] if row_nombre else ''
            
            # Restaurar el stock del producto
            cursor.execute(
                'UPDATE productos SET stock = stock + %s WHERE id = %s',
                (cantidad, producto_id)
            )
            
            # Si es maple huevo, también restaurar huevo unidad
            if nombre_producto.lower() == 'maple huevo':
                self._ajustar_huevo_unidad(cursor, cantidad * HUEVOS_POR_MAPLE)
            
            # Eliminar la venta
            cursor.execute(
                'DELETE FROM ventas WHERE id = %s',
                (venta_id,)
            )
            
            conn.commit()
            logger.info(f"Venta {venta_id} eliminada y stock restaurado (+{cantidad})")
            return True
            
        except ErrorValidacionError:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar venta {venta_id}: {str(e)}")
            raise ErrorTransaccionError("eliminar_venta", str(e))
        finally:
            conn.close()
    
    def obtener_venta_por_id(self, venta_id: int) -> Optional[Venta]:
        """
        Obtener una venta específica por ID
        
        Args:
            venta_id: ID de la venta
        
        Returns:
            Objeto Venta o None si no existe
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''SELECT id, producto_id, cantidad, precio_unitario, 
                   costo_unitario, ganancia_unitaria, fecha
                   FROM ventas
                   WHERE id = %s''',
                (venta_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            venta = Venta(
                id=row[0],
                producto_id=row[1],
                cantidad=row[2],
                precio_unitario=row[3],
                costo_unitario=row[4],
                ganancia_unitaria=row[5],
                fecha=row[6],
                mes_contable=None
            )
            return venta
        finally:
            conn.close()
    
    def editar_venta(
        self,
        venta_id: int,
        cantidad: float,
        precio_unitario: float,
        fecha: str = None
    ) -> bool:
        """
        Editar una venta existente y ajustar el stock
        
        Args:
            venta_id: ID de la venta a editar
            cantidad: Nueva cantidad
            precio_unitario: Nuevo precio unitario
            fecha: Nueva fecha (opcional, formato YYYY-MM-DD HH:MM:SS)
        
        Returns:
            True si se editó correctamente
            
        Raises:
            ErrorValidacionError: Si datos son inválidos
            StockInsuficienteError: Si no hay stock suficiente
        """
        # Validar entrada
        if cantidad <= 0:
            raise ErrorValidacionError("cantidad", cantidad, "Debe ser mayor a 0")
        
        if precio_unitario < 0:
            raise ErrorValidacionError("precio_unitario", precio_unitario, "No puede ser negativo")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener datos actuales de la venta
            cursor.execute(
                'SELECT producto_id, cantidad FROM ventas WHERE id = %s',
                (venta_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                raise ErrorValidacionError("venta_id", venta_id, "La venta no existe")
            
            producto_id, cantidad_anterior = row[0], row[1]
            
            # Obtener datos del producto
            cursor.execute(
                'SELECT stock, costo_unitario FROM productos WHERE id = %s',
                (producto_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise ProductoNoEncontradoError(f"ID {producto_id}")
            
            stock, costo_unitario = row[0], row[1]
            
            # Calcular diferencia de stock
            diferencia_stock = cantidad - cantidad_anterior
            
            # Validar stock disponible si se aumenta la cantidad
            if diferencia_stock > 0 and diferencia_stock > stock:
                raise StockInsuficienteError(f"Producto ID {producto_id}", diferencia_stock, stock)
            
            # Calcular nueva ganancia
            ganancia_unitaria = precio_unitario - costo_unitario
            
            # Actualizar la venta (con o sin fecha)
            if fecha:
                cursor.execute(
                    '''UPDATE ventas 
                       SET cantidad = %s, precio_unitario = %s, ganancia_unitaria = %s, fecha = %s
                       WHERE id = %s''',
                    (cantidad, precio_unitario, ganancia_unitaria, fecha, venta_id)
                )
            else:
                cursor.execute(
                    '''UPDATE ventas 
                       SET cantidad = %s, precio_unitario = %s, ganancia_unitaria = %s
                       WHERE id = %s''',
                    (cantidad, precio_unitario, ganancia_unitaria, venta_id)
                )
            
            # Obtener nombre del producto para verificar si es maple
            cursor.execute(
                'SELECT nombre FROM productos WHERE id = %s',
                (producto_id,)
            )
            row_nombre = cursor.fetchone()
            nombre_producto = row_nombre[0] if row_nombre else ''
            
            # Ajustar stock del producto
            cursor.execute(
                'UPDATE productos SET stock = stock - %s WHERE id = %s',
                (diferencia_stock, producto_id)
            )
            
            # Si es maple huevo, también ajustar huevo unidad
            if nombre_producto.lower() == 'maple huevo':
                self._ajustar_huevo_unidad(cursor, -diferencia_stock * HUEVOS_POR_MAPLE)
            
            conn.commit()
            logger.info(f"Venta {venta_id} editada: cantidad {cantidad_anterior} → {cantidad}, ajuste stock: {-diferencia_stock}")
            return True
            
        except (ErrorValidacionError, StockInsuficienteError, ProductoNoEncontradoError):
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al editar venta {venta_id}: {str(e)}")
            raise ErrorTransaccionError("editar_venta", str(e))
        finally:
            conn.close()
    
    def _ajustar_huevo_unidad(self, cursor, cantidad: float) -> None:
        """
        Ajustar stock de huevo unidad (método auxiliar)
        
        Args:
            cursor: Cursor de base de datos
            cantidad: Cantidad a ajustar (positiva para agregar, negativa para restar)
        """
        # Buscar el producto huevo unidad
        cursor.execute(
            'SELECT id, stock FROM productos WHERE nombre = %s',
            ('huevo unidad',)
        )
        row = cursor.fetchone()
        
        if row:
            huevo_id, stock_actual = row[0], row[1]
            nuevo_stock = stock_actual + cantidad
            
            cursor.execute(
                'UPDATE productos SET stock = %s WHERE id = %s',
                (nuevo_stock, huevo_id)
            )
            
            logger.info(
                f"Ajuste automático huevo unidad: {stock_actual} + {cantidad} = {nuevo_stock}"
            )
        else:
            logger.warning("No se encontró producto 'huevo unidad' para ajustar")


# =============================================================================
# Funciones wrapper para compatibilidad con Desktop (legacy)
# TODO: Migrar Desktop a usar VentasService() directamente
# =============================================================================

def registrar_venta(datos: dict) -> dict:
    """
    DEPRECATED: Tkinter desktop support removed (2026-02-13)
    Wrapper function maintained for backward compatibility
    
    Args:
        datos: dict con keys: producto_id, cantidad, precio_venta, usuario_id
    
    Returns:
        dict con {'exito': bool, 'mensaje': str, 'ganancia': float}
    """
    from backend.services.productos_service import ProductosService
    
    try:
        # Obtener producto
        productos_service = ProductosService()
        producto = productos_service.obtener_producto_por_id(datos['producto_id'])
        
        if not producto:
            return {'exito': False, 'mensaje': 'Producto no encontrado', 'ganancia': 0}
        
        # Registrar venta
        ventas_service = VentasService()
        exito, mensaje, ganancia = ventas_service.registrar_venta(
            nombre_producto=producto.nombre,
            cantidad=datos['cantidad'],
            precio_unitario=datos['precio_venta'],
            forma_pago=datos.get('forma_pago', 'efectivo')
        )
        
        return {'exito': exito, 'mensaje': mensaje, 'ganancia': ganancia}
    
    except Exception as e:
        logger.error(f"Error en registrar_venta wrapper: {str(e)}")
        return {'exito': False, 'mensaje': str(e), 'ganancia': 0}


def obtener_ventas_recientes(limite: int = 20) -> list:
    """
    DEPRECATED: Tkinter desktop support removed (2026-02-13)
    Wrapper function maintained for backward compatibility
    
    Args:
        limite: Número máximo de ventas a retornar
    
    Returns:
        Lista de diccionarios con datos de ventas
    """
    ventas_service = VentasService()
    ventas = ventas_service.obtener_todas_ventas()
    
    # Convertir objetos Venta a diccionarios y limitar
    resultados = [
        {
            'id': v['id'],
            'fecha': v['fecha'],
            'producto_nombre': v['nombre'],
            'cantidad': v['cantidad'],
            'precio_venta': v['precio_unitario'],
            'ganancia': v['ganancia_unitaria']
        }
        for v in ventas
    ]
    
    # Retornar solo las últimas 'limite' ventas
    return resultados[:limite]
