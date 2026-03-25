"""
Servicio de gestión de compras
Lógica de negocio para compras e inventario
"""
import logging
from datetime import datetime
from typing import Optional, Tuple, List

from backend.database.connection import DatabaseConnection
from backend.models.compra import Compra
from backend.services.productos_service import ProductosService
from backend.utils.exceptions import (
    ProductoNoEncontradoError,
    ErrorTransaccionError,
    ErrorValidacionError,
)

logger = logging.getLogger(__name__)

# Constante para relación maple huevo - huevo unidad
HUEVOS_POR_MAPLE = 30


class ComprasService:
    """Servicio para gestionar compras de productos"""
    
    def __init__(self) -> None:
        self.db = DatabaseConnection.get_instance()
        self.productos_service = ProductosService()
        logger.debug("ComprasService inicializado")
    
    def registrar_compra(
        self,
        nombre_producto: str,
        cantidad: float,
        costo_unitario: float
    ) -> Tuple[bool, str]:
        """
        Registrar una compra de producto
        Actualiza el stock y calcula el costo promedio ponderado
        
        Args:
            nombre_producto: Nombre del producto
            cantidad: Cantidad comprada (puede ser decimal para kg)
            costo_unitario: Costo por unidad
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        
        Raises:
            ErrorValidacionError: Si datos son inválidos
            ProductoNoEncontradoError: Si el producto no existe
        """
        # Validar entrada
        if cantidad <= 0:
            raise ErrorValidacionError("cantidad", cantidad, "Debe ser mayor a 0")
        
        if costo_unitario < 0:
            raise ErrorValidacionError("costo_unitario", costo_unitario, "No puede ser negativo")
        
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
                logger.warning(f"Intento de compra para producto inexistente: {nombre_producto}")
                raise ProductoNoEncontradoError(nombre_producto)
            
            producto_id, stock_anterior, costo_anterior = row[0], row[1], row[2]
            
            # Registrar la compra usando hora local
            cursor.execute(
                'INSERT INTO compras (producto_id, cantidad, costo_unitario, fecha) VALUES (%s, %s, %s, %s)',
                (producto_id, cantidad, costo_unitario, datetime.now())
            )
            
            # Calcular nuevo costo promedio ponderado
            nuevo_costo = self._calcular_costo_promedio(
                producto_id, cantidad, costo_unitario, stock_anterior, costo_anterior
            )
            
            # Actualizar stock y costo del producto
            cursor.execute(
                'UPDATE productos SET stock = stock + %s, costo_unitario = %s WHERE id = %s',
                (cantidad, nuevo_costo, producto_id)
            )
            
            # Si es maple huevo, también actualizar huevo unidad
            if nombre_producto.lower() == 'maple huevo':
                self._ajustar_huevo_unidad(cursor, cantidad * HUEVOS_POR_MAPLE)
            
            conn.commit()
            
            mensaje = f'Compra registrada. Nuevo costo unitario: ${nuevo_costo:.2f}'
            logger.info(
                f"Compra registrada: {nombre_producto} x{cantidad} @ ${costo_unitario:.2f} "
                f"-> Costo promedio: ${nuevo_costo:.2f}"
            )
            return True, mensaje
        
        except ProductoNoEncontradoError:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al registrar compra de {nombre_producto}: {str(e)}")
            raise ErrorTransaccionError("registrar_compra", str(e))
        finally:
            conn.close()
    
    def _calcular_costo_promedio(
        self,
        producto_id: int,
        cantidad_nueva: int,
        costo_nuevo: float,
        stock_anterior: int,
        costo_anterior: float
    ) -> float:
        """
        Calcular costo promedio ponderado
        
        Fórmula:
        Nuevo Costo = (Stock_anterior × Costo_anterior + Cantidad_nueva × Costo_nuevo) 
                      / (Stock_anterior + Cantidad_nueva)
        
        Args:
            producto_id: ID del producto
            cantidad_nueva: Cantidad nueva a agregar
            costo_nuevo: Costo de la nueva compra
            stock_anterior: Stock anterior
            costo_anterior: Costo anterior
        
        Returns:
            Nuevo costo promedio redondeado a 2 decimales
        """
        if stock_anterior <= 0:
            logger.debug(f"Primer compra de producto {producto_id}, costo: ${costo_nuevo:.2f}")
            return round(costo_nuevo, 2)
        
        total_cantidad = stock_anterior + cantidad_nueva
        costo_promedio = (
            (stock_anterior * costo_anterior) + (cantidad_nueva * costo_nuevo)
        ) / total_cantidad
        
        resultado = round(costo_promedio, 2)
        logger.debug(
            f"Costo promedio calculado: ({stock_anterior}×${costo_anterior:.2f} + "
            f"{cantidad_nueva}×${costo_nuevo:.2f}) / {total_cantidad} = ${resultado:.2f}"
        )
        return resultado
    
    def obtener_historial_compras(self, nombre_producto: str) -> List[dict]:
        """
        Obtener historial de compras de un producto
        
        Args:
            nombre_producto: Nombre del producto
        
        Returns:
            Lista de compras
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''SELECT compras.id, compras.cantidad, compras.costo_unitario, 
                   compras.fecha FROM compras
                   JOIN productos ON compras.producto_id = productos.id
                   WHERE productos.nombre = ?
                   ORDER BY compras.fecha DESC, compras.id DESC''',
                (nombre_producto,)
            )
            colnames = [desc[0] for desc in cursor.description]
            compras = [dict(zip(colnames, row)) for row in cursor.fetchall()]
            logger.debug(f"Consultado historial de {len(compras)} compras para {nombre_producto}")
            return compras
        finally:
            conn.close()
    
    def listar_compras(self) -> List[Compra]:
        """
        Listar todas las compras como objetos Compra
        
        Returns:
            Lista de objetos Compra
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar si existe columna mes_contable
            try:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'compras';")
                columnas = [col[0] for col in cursor.fetchall()]
            except Exception:
                cursor.execute("PRAGMA table_info(compras)")
                columnas = [col[1] for col in cursor.fetchall()]
            tiene_mes_contable = 'mes_contable' in columnas
            
            if tiene_mes_contable:
                cursor.execute(
                    '''SELECT id, producto_id, cantidad, costo_unitario, fecha, mes_contable
                       FROM compras
                       ORDER BY fecha DESC'''
                )
            else:
                cursor.execute(
                    '''SELECT id, producto_id, cantidad, costo_unitario, fecha
                       FROM compras
                       ORDER BY fecha DESC'''
                )
            
            compras = []
            for row in cursor.fetchall():
                if tiene_mes_contable:
                    compra = Compra(
                        id=row[0],
                        producto_id=row[1],
                        cantidad=row[2],
                        costo_unitario=row[3],
                        fecha=row[4],
                        mes_contable=row[5]
                    )
                else:
                    compra = Compra(
                        id=row[0],
                        producto_id=row[1],
                        cantidad=row[2],
                        costo_unitario=row[3],
                        fecha=row[4],
                        mes_contable=None
                    )
                compras.append(compra)
            logger.debug(f"Listadas {len(compras)} compras")
            return compras
        finally:
            conn.close()
    
    def obtener_compras_por_fecha(self, fecha: str) -> List[Compra]:
        """
        Obtener compras de una fecha específica
        
        Args:
            fecha: Fecha en formato YYYY-MM-DD
        
        Returns:
            Lista de objetos Compra
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar si existe columna mes_contable
            try:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'compras';")
                columnas = [col[0] for col in cursor.fetchall()]
            except Exception:
                cursor.execute("PRAGMA table_info(compras)")
                columnas = [col[1] for col in cursor.fetchall()]
            tiene_mes_contable = 'mes_contable' in columnas
            
            if tiene_mes_contable:
                cursor.execute(
                    '''SELECT id, producto_id, cantidad, costo_unitario, fecha, mes_contable
                       FROM compras
                       WHERE DATE(fecha) = %s
                       ORDER BY fecha DESC''',
                    (fecha,)
                )
            else:
                cursor.execute(
                    '''SELECT id, producto_id, cantidad, costo_unitario, fecha
                       FROM compras
                       WHERE DATE(fecha) = %s
                       ORDER BY fecha DESC''',
                    (fecha,)
                )
            
            compras = []
            for row in cursor.fetchall():
                if tiene_mes_contable:
                    compra = Compra(
                        id=row[0],
                        producto_id=row[1],
                        cantidad=row[2],
                        costo_unitario=row[3],
                        fecha=row[4],
                        mes_contable=row[5]
                    )
                else:
                    compra = Compra(
                        id=row[0],
                        producto_id=row[1],
                        cantidad=row[2],
                        costo_unitario=row[3],
                        fecha=row[4],
                        mes_contable=None
                    )
                compras.append(compra)
            logger.debug(f"Listadas {len(compras)} compras para fecha {fecha}")
            return compras
        finally:
            conn.close()
    
    def eliminar_compra(self, compra_id: int) -> tuple[bool, str]:
        """
        Eliminar una compra y ajustar el stock
        NOTA: Permite eliminar aunque el stock quede negativo (si ya se vendió parte)
        
        Args:
            compra_id: ID de la compra a eliminar
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje_advertencia)
            
        Raises:
            ErrorTransaccionError: Si hay error en la transacción
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener datos de la compra antes de eliminar
            cursor.execute(
                'SELECT producto_id, cantidad FROM compras WHERE id = %s',
                (compra_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"Intento de eliminar compra inexistente: ID {compra_id}")
                raise ErrorValidacionError("compra_id", compra_id, "La compra no existe")
            
            producto_id, cantidad = row[0], row[1]
            
            # Verificar stock actual
            cursor.execute(
                'SELECT stock, nombre FROM productos WHERE id = %s',
                (producto_id,)
            )
            row = cursor.fetchone()
            stock_actual = row[0] if row else 0
            nombre_producto = row[1] if row and len(row) > 1 else "Producto"
            
            # Calcular nuevo stock
            nuevo_stock = stock_actual - cantidad
            mensaje = ""
            
            if nuevo_stock < 0:
                # Advertencia: el stock quedará negativo
                vendidas = abs(nuevo_stock)
                mensaje = f"⚠️ ADVERTENCIA: Ya se vendieron {vendidas} unidad(es) de esta compra. Stock quedará en {nuevo_stock}"
                logger.warning(f"Eliminando compra {compra_id}: stock quedará negativo ({nuevo_stock}) para {nombre_producto}")
            
            # Reducir el stock del producto (permite negativos)
            cursor.execute(
                'UPDATE productos SET stock = stock - %s WHERE id = %s',
                (cantidad, producto_id)
            )
            
            # Si es maple huevo, también ajustar huevo unidad
            if nombre_producto.lower() == 'maple huevo':
                self._ajustar_huevo_unidad(cursor, -cantidad * HUEVOS_POR_MAPLE)
            
            # Eliminar la compra
            cursor.execute(
                'DELETE FROM compras WHERE id = %s',
                (compra_id,)
            )
            
            conn.commit()
            logger.info(f"Compra {compra_id} eliminada y stock ajustado (-{cantidad}, nuevo stock: {nuevo_stock})")
            return True, mensaje
            
        except ErrorValidacionError:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar compra {compra_id}: {str(e)}")
            raise ErrorTransaccionError("eliminar_compra", str(e))
        finally:
            conn.close()
    
    def obtener_compra_por_id(self, compra_id: int) -> Optional[Compra]:
        """
        Obtener una compra específica por ID
        
        Args:
            compra_id: ID de la compra
        
        Returns:
            Objeto Compra o None si no existe
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar si existe columna mes_contable
            try:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'compras';")
                columnas = [col[0] for col in cursor.fetchall()]
            except Exception:
                cursor.execute("PRAGMA table_info(compras)")
                columnas = [col[1] for col in cursor.fetchall()]
            tiene_mes_contable = 'mes_contable' in columnas
            
            if tiene_mes_contable:
                cursor.execute(
                    '''SELECT id, producto_id, cantidad, costo_unitario, fecha, mes_contable
                       FROM compras
                       WHERE id = ?''',
                    (compra_id,)
                )
            else:
                cursor.execute(
                    '''SELECT id, producto_id, cantidad, costo_unitario, fecha
                       FROM compras
                       WHERE id = ?''',
                    (compra_id,)
                )
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            if tiene_mes_contable:
                compra = Compra(
                    id=row[0],
                    producto_id=row[1],
                    cantidad=row[2],
                    costo_unitario=row[3],
                    fecha=row[4],
                    mes_contable=row[5]
                )
            else:
                compra = Compra(
                    id=row[0],
                    producto_id=row[1],
                    cantidad=row[2],
                    costo_unitario=row[3],
                    fecha=row[4],
                    mes_contable=None
                )
            return compra
        finally:
            conn.close()
    
    def editar_compra(
        self,
        compra_id: int,
        cantidad: float,
        costo_unitario: float,
        fecha: str = None
    ) -> bool:
        """
        Editar una compra existente y ajustar el stock
        NOTA: No recalcula el costo promedio, solo ajusta cantidad y stock
        
        Args:
            compra_id: ID de la compra a editar
            cantidad: Nueva cantidad
            costo_unitario: Nuevo costo unitario
            fecha: Nueva fecha (opcional, formato YYYY-MM-DD HH:MM:SS)
        
        Returns:
            True si se editó correctamente
            
        Raises:
            ErrorValidacionError: Si datos son inválidos
        """
        # Validar entrada
        if cantidad <= 0:
            raise ErrorValidacionError("cantidad", cantidad, "Debe ser mayor a 0")
        
        if costo_unitario < 0:
            raise ErrorValidacionError("costo_unitario", costo_unitario, "No puede ser negativo")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener datos actuales de la compra
            cursor.execute(
                'SELECT producto_id, cantidad FROM compras WHERE id = ?',
                (compra_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                raise ErrorValidacionError("compra_id", compra_id, "La compra no existe")
            
            producto_id, cantidad_anterior = row[0], row[1]
            
            # Calcular diferencia de stock
            diferencia_stock = cantidad - cantidad_anterior
            
            # Si se reduce la cantidad, verificar que hay suficiente stock
            if diferencia_stock < 0:
                cursor.execute(
                    'SELECT stock FROM productos WHERE id = ?',
                    (producto_id,)
                )
                row = cursor.fetchone()
                stock_actual = row[0] if row else 0
                
                if abs(diferencia_stock) > stock_actual:
                    raise ErrorValidacionError(
                        "stock",
                        stock_actual,
                        f"No hay suficiente stock para reducir la compra (requiere {abs(diferencia_stock)}, disponible {stock_actual})"
                    )
            
            # Actualizar la compra (con o sin fecha)
            if fecha:
                cursor.execute(
                    '''UPDATE compras 
                       SET cantidad = ?, costo_unitario = ?, fecha = ?
                       WHERE id = ?''',
                    (cantidad, costo_unitario, fecha, compra_id)
                )
            else:
                cursor.execute(
                    '''UPDATE compras 
                       SET cantidad = ?, costo_unitario = ?
                       WHERE id = ?''',
                    (cantidad, costo_unitario, compra_id)
                )
            
            # Obtener nombre del producto para verificar si es maple
            cursor.execute(
                'SELECT nombre FROM productos WHERE id = ?',
                (producto_id,)
            )
            row_nombre = cursor.fetchone()
            nombre_producto = row_nombre[0] if row_nombre else ''
            
            # Ajustar stock del producto
            cursor.execute(
                'UPDATE productos SET stock = stock + ? WHERE id = ?',
                (diferencia_stock, producto_id)
            )
            
            # Si es maple huevo, también ajustar huevo unidad
            if nombre_producto.lower() == 'maple huevo':
                self._ajustar_huevo_unidad(cursor, diferencia_stock * HUEVOS_POR_MAPLE)
            
            conn.commit()
            logger.info(f"Compra {compra_id} editada: cantidad {cantidad_anterior} → {cantidad}, ajuste stock: {diferencia_stock}")
            return True
            
        except ErrorValidacionError:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al editar compra {compra_id}: {str(e)}")
            raise ErrorTransaccionError("editar_compra", str(e))
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
            'SELECT id, stock FROM productos WHERE nombre = ?',
            ('huevo unidad',)
        )
        row = cursor.fetchone()
        
        if row:
            huevo_id, stock_actual = row[0], row[1]
            nuevo_stock = stock_actual + cantidad
            
            cursor.execute(
                'UPDATE productos SET stock = ? WHERE id = ?',
                (nuevo_stock, huevo_id)
            )
            
            logger.info(
                f"Ajuste automático huevo unidad: {stock_actual} + {cantidad} = {nuevo_stock}"
            )
        else:
            logger.warning("No se encontró producto 'huevo unidad' para ajustar")
    
    def obtener_todas_compras(self) -> List[Compra]:
        """
        Obtener todas las compras registradas
        
        Returns:
            Lista de objetos Compra
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar si existe columna mes_contable en compras
        try:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'compras';")
            columnas = [col[0] for col in cursor.fetchall()]
        except Exception:
            cursor.execute("PRAGMA table_info(compras)")
            columnas = [col[1] for col in cursor.fetchall()]
        tiene_mes_contable = 'mes_contable' in columnas
        
        if tiene_mes_contable:
            cursor.execute('''
                SELECT c.id, c.producto_id, c.cantidad, c.costo_unitario, c.fecha, c.mes_contable,
                       p.nombre, p.stock, p.costo_unitario
                FROM compras c
                JOIN productos p ON c.producto_id = p.id
                ORDER BY c.fecha DESC
            ''')
        else:
            # Consulta sin mes_contable para compatibilidad
            cursor.execute('''
                SELECT c.id, c.producto_id, c.cantidad, c.costo_unitario, c.fecha,
                       p.nombre, p.stock, p.costo_unitario
                FROM compras c
                JOIN productos p ON c.producto_id = p.id
                ORDER BY c.fecha DESC
            ''')
        
        compras = []
        for row in cursor.fetchall():
            if tiene_mes_contable:
                compra = Compra(
                    producto_id=row[1],
                    cantidad=row[2],
                    costo_unitario=row[3],
                    mes_contable=row[5] if row[5] else None
                )
                compra.id = row[0]
                compra.fecha = row[4]
                
                # Crear objeto producto simplificado
                from backend.models.producto import Producto
                producto = Producto(
                    nombre=row[6],
                    stock=row[7],
                    costo_unitario=row[8]
                )
                compra.producto = producto
            else:
                # Sin mes_contable
                compra = Compra(
                    producto_id=row[1],
                    cantidad=row[2],
                    costo_unitario=row[3],
                    mes_contable=None
                )
                compra.id = row[0]
                compra.fecha = row[4]
                
                # Crear objeto producto simplificado
                from backend.models.producto import Producto
                producto = Producto(
                    nombre=row[5],
                    stock=row[6],
                    costo_unitario=row[7]
                )
                compra.producto = producto
            
            compras.append(compra)
        
        return compras


# =============================================================================
# Funciones wrapper para compatibilidad con Desktop (legacy)
# TODO: Migrar Desktop a usar ComprasService() directamente
# =============================================================================

def registrar_compra(datos: dict) -> dict:
    """
    DEPRECATED: Tkinter desktop support removed (2026-02-13)
    Wrapper function maintained for backward compatibility
    
    Args:
        datos: dict con keys: producto_id, cantidad, precio_compra, usuario_id
    
    Returns:
        dict con {'exito': bool, 'mensaje': str}
    """
    from backend.services.productos_service import ProductosService
    
    try:
        # Obtener producto
        productos_service = ProductosService()
        producto = productos_service.obtener_producto_por_id(datos['producto_id'])
        
        if not producto:
            return {'exito': False, 'mensaje': 'Producto no encontrado'}
        
        # Registrar compra
        compras_service = ComprasService()
        exito, mensaje = compras_service.registrar_compra(
            nombre_producto=producto.nombre,
            cantidad=datos['cantidad'],
            costo_unitario=datos['precio_compra']
        )
        
        return {'exito': exito, 'mensaje': mensaje}
    
    except Exception as e:
        logger.error(f"Error en registrar_compra wrapper: {str(e)}")
        return {'exito': False, 'mensaje': str(e)}


def obtener_compras_recientes(limite: int = 20) -> list:
    """
    DEPRECATED: Tkinter desktop support removed (2026-02-13)
    Wrapper function maintained for backward compatibility
    
    Args:
        limite: Número máximo de compras a retornar
    
    Returns:
        Lista de diccionarios con datos de compras
    """
    compras_service = ComprasService()
    compras = compras_service.obtener_todas_compras()
    
    # Convertir objetos Compra a diccionarios y limitar
    resultados = [
        {
            'id': c.id,
            'fecha': c.fecha,
            'producto_nombre': c.producto.nombre if c.producto else 'Desconocido',
            'cantidad': c.cantidad,
            'precio_compra': c.costo_unitario
        }
        for c in compras
    ]
    
    # Retornar solo las últimas 'limite' compras
    return resultados[:limite]
