"""
Servicio de Inventario Valorizado
Implementa Promedio Ponderado Móvil para cálculo de costos
"""
import logging
from datetime import datetime
from typing import Optional, Dict

from backend.database.connection import DatabaseConnection
from backend.models.contabilidad import InventoryMovement
from backend.utils.enums import MovementType
from backend.utils.exceptions import ErrorValidacionError

logger = logging.getLogger(__name__)


class InventarioService:
    """Servicio para gestionar inventario valorizado con Promedio Ponderado Móvil"""
    
    def __init__(self) -> None:
        self.db = DatabaseConnection.get_instance()
        logger.debug("InventarioService inicializado")
    
    def calcular_costo_promedio_ponderado(
        self,
        producto_id: int,
        cantidad_nueva: float,
        costo_nuevo: float
    ) -> float:
        """
        Calcular costo promedio ponderado después de una compra
        
        Fórmula: CPP = (Stock_Anterior * Costo_Anterior + Cantidad_Nueva * Costo_Nuevo) 
                       / (Stock_Anterior + Cantidad_Nueva)
        
        Args:
            producto_id: ID del producto
            cantidad_nueva: Cantidad comprada
            costo_nuevo: Costo unitario de la compra
        
        Returns:
            Nuevo costo promedio ponderado
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener stock y costo actual
            cursor.execute(
                'SELECT stock, costo_unitario FROM productos WHERE id = %s',
                (producto_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                raise ErrorValidacionError(f"Producto {producto_id} no existe")
            
            stock_anterior = row[0]
            costo_anterior = row[1]
            
            # Si no hay stock previo, el nuevo costo es el costo de esta compra
            if stock_anterior <= 0:
                return costo_nuevo
            
            # Calcular promedio ponderado
            valor_anterior = stock_anterior * costo_anterior
            valor_nuevo = cantidad_nueva * costo_nuevo
            stock_total = stock_anterior + cantidad_nueva
            
            costo_promedio = (valor_anterior + valor_nuevo) / stock_total
            
            logger.debug(
                f"Costo promedio calculado para producto {producto_id}: "
                f"${costo_anterior:.2f} -> ${costo_promedio:.2f}"
            )
            
            return costo_promedio
            
        finally:
            conn.close()
    
    def registrar_entrada_inventario(
        self,
        producto_id: int,
        cantidad: float,
        costo_unitario: float,
        descripcion: str = "Compra",
        reference_table: Optional[str] = "compras",
        reference_id: Optional[int] = None
    ) -> int:
        """
        Registrar entrada de inventario (compra)
        
        Args:
            producto_id: ID del producto
            cantidad: Cantidad comprada
            costo_unitario: Costo por unidad
            descripcion: Descripción del movimiento
            reference_table: Tabla de referencia
            reference_id: ID de referencia
        
        Returns:
            ID del movimiento creado
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener estado actual
            cursor.execute(
                'SELECT stock, costo_unitario FROM productos WHERE id = %s',
                (producto_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                raise ErrorValidacionError(f"Producto {producto_id} no existe")
            
            stock_anterior = row[0]
            costo_anterior = row[1]
            
            # Calcular nuevo costo promedio
            costo_promedio_nuevo = self.calcular_costo_promedio_ponderado(
                producto_id, cantidad, costo_unitario
            )
            
            stock_nuevo = stock_anterior + cantidad
            
            # Registrar movimiento
            cursor.execute(
                '''INSERT INTO inventory_movements 
                   (producto_id, movement_type, cantidad, costo_unitario, fecha,
                    reference_table, reference_id, descripcion,
                    stock_anterior, stock_nuevo, costo_promedio_anterior, costo_promedio_nuevo)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (producto_id, MovementType.ENTRADA.value, cantidad, costo_unitario,
                 datetime.now(), reference_table, reference_id, descripcion,
                 stock_anterior, stock_nuevo, costo_anterior, costo_promedio_nuevo)
            )
            
            movement_id = cursor.lastrowid
            conn.commit()
            
            logger.info(
                f"Entrada inventario registrada: Producto {producto_id}, "
                f"Cantidad {cantidad}, Nuevo CPP: ${costo_promedio_nuevo:.2f}"
            )
            
            return movement_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error registrando entrada inventario: {str(e)}")
            raise
        finally:
            conn.close()
    
    def registrar_salida_inventario(
        self,
        producto_id: int,
        cantidad: float,
        descripcion: str = "Venta",
        reference_table: Optional[str] = "ventas",
        reference_id: Optional[int] = None
    ) -> tuple[int, float]:
        """
        Registrar salida de inventario (venta)
        
        Args:
            producto_id: ID del producto
            cantidad: Cantidad vendida
            descripcion: Descripción del movimiento
            reference_table: Tabla de referencia
            reference_id: ID de referencia
        
        Returns:
            Tupla (movement_id, costo_unitario_usado)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener estado actual
            cursor.execute(
                'SELECT stock, costo_unitario FROM productos WHERE id = %s',
                (producto_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                raise ErrorValidacionError(f"Producto {producto_id} no existe")
            
            stock_anterior = row[0]
            costo_actual = row[1]
            
            # Validar stock suficiente
            if stock_anterior < cantidad:
                raise ErrorValidacionError(
                    f"Stock insuficiente: disponible={stock_anterior}, requerido={cantidad}"
                )
            
            stock_nuevo = stock_anterior - cantidad
            
            # Registrar movimiento (costo promedio no cambia en ventas)
            cursor.execute(
                '''INSERT INTO inventory_movements 
                   (producto_id, movement_type, cantidad, costo_unitario, fecha,
                    reference_table, reference_id, descripcion,
                    stock_anterior, stock_nuevo, costo_promedio_anterior, costo_promedio_nuevo)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (producto_id, MovementType.SALIDA.value, cantidad, costo_actual,
                 datetime.now(), reference_table, reference_id, descripcion,
                 stock_anterior, stock_nuevo, costo_actual, costo_actual)
            )
            
            movement_id = cursor.lastrowid
            conn.commit()
            
            logger.info(
                f"Salida inventario registrada: Producto {producto_id}, "
                f"Cantidad {cantidad}, Costo usado: ${costo_actual:.2f}"
            )
            
            return movement_id, costo_actual
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error registrando salida inventario: {str(e)}")
            raise
        finally:
            conn.close()
    
    def obtener_valorizado_producto(self, producto_id: int) -> Dict:
        """
        Obtener valorización actual de un producto
        
        Args:
            producto_id: ID del producto
        
        Returns:
            Dict con stock, costo_promedio, valor_total
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''SELECT p.id, p.nombre, p.stock, p.costo_unitario
                   FROM productos p
                   WHERE p.id = %s''',
                (producto_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                raise ErrorValidacionError(f"Producto {producto_id} no existe")
            
            stock = row[2]
            costo_promedio = row[3]
            valor_total = stock * costo_promedio
            
            return {
                'producto_id': row[0],
                'nombre': row[1],
                'stock': stock,
                'costo_promedio': costo_promedio,
                'valor_total': valor_total
            }
            
        finally:
            conn.close()
    
    def obtener_inventario_valorizado_total(self) -> Dict:
        """
        Obtener inventario valorizado completo
        
        Returns:
            Dict con productos y totales
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''SELECT id, nombre, stock, costo_unitario
                   FROM productos
                   ORDER BY nombre'''
            )

            productos = []
            valor_total = 0.0

            for row in cursor.fetchall():
                stock = float(row[2])
                costo_promedio = float(row[3])
                valor_producto = float(stock * costo_promedio)

                productos.append({
                    'id': row[0],
                    'nombre': row[1],
                    'stock': stock,
                    'costo_promedio': costo_promedio,
                    'valor_total': valor_producto
                })

                valor_total += valor_producto

            logger.debug(f"Inventario valorizado: {len(productos)} productos, valor ${valor_total:.2f}")

            return {
                'productos': productos,
                'valor_total': valor_total,
                'fecha_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        finally:
            conn.close()
