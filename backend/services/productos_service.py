"""
Servicio de gestión de productos
Lógica de negocio para operaciones con productos
"""
import logging
from typing import List, Optional, Tuple

from backend.database.connection import DatabaseConnection
from backend.models.producto import Producto
from backend.config.settings import PRODUCTOS_INICIALES
from backend.utils.exceptions import (
    ProductoNoEncontradoError,
    ErrorTransaccionError,
    ErrorValidacionError,
)

logger = logging.getLogger(__name__)


class ProductosService:
    """Servicio para gestionar productos"""
    
    def __init__(self) -> None:
        self.db = DatabaseConnection.get_instance()
        logger.debug("ProductosService inicializado")
    
    def crear_producto(
        self,
        nombre: str,
        stock: int = 0,
        costo_unitario: float = 0.0
    ) -> Producto:
        """
        Crear un nuevo producto
        
        Args:
            nombre: Nombre único del producto
            stock: Stock inicial
            costo_unitario: Costo unitario inicial
        
        Returns:
            Producto creado
        
        Raises:
            ErrorTransaccionError: Si falla la creación
        """
        if not nombre or not isinstance(nombre, str):
            raise ErrorValidacionError("nombre", nombre, "Debe ser un texto no vacío")
        
        if stock < 0:
            raise ErrorValidacionError("stock", stock, "No puede ser negativo")
        
        if costo_unitario < 0:
            raise ErrorValidacionError("costo_unitario", costo_unitario, "No puede ser negativo")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO productos (nombre, stock, costo_unitario) VALUES (?, ?, ?)',
                (nombre, stock, costo_unitario)
            )
            conn.commit()
            logger.info(f"Producto creado: {nombre}")
            
            # Obtener el producto creado
            cursor.execute(
                'SELECT id, nombre, stock, costo_unitario, margen_porcentaje, precio_sugerido '
                'FROM productos WHERE nombre = ?',
                (nombre,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_producto(row)
        except Exception as e:
            logger.error(f"Error al crear producto {nombre}: {str(e)}")
            raise ErrorTransaccionError("crear_producto", str(e))
        finally:
            conn.close()
        
        return Producto(nombre=nombre, stock=stock, costo_unitario=costo_unitario)
    
    def obtener_producto_por_nombre(self, nombre: str) -> Optional[Producto]:
        """
        Obtener un producto por nombre
        
        Args:
            nombre: Nombre del producto
        
        Returns:
            Producto si existe, None si no
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT id, nombre, stock, costo_unitario, margen_porcentaje, precio_sugerido '
                'FROM productos WHERE LOWER(nombre) = LOWER(?)',
                (nombre,)
            )
            row = cursor.fetchone()
            logger.debug(f"Consultado producto: {nombre}")
            return self._row_to_producto(row) if row else None
        finally:
            conn.close()
    
    def obtener_producto_por_id(self, producto_id: int) -> Optional[Producto]:
        """
        Obtener un producto por ID
        
        Args:
            producto_id: ID del producto
        
        Returns:
            Producto si existe, None si no
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT id, nombre, stock, costo_unitario, margen_porcentaje, precio_sugerido '
                'FROM productos WHERE id = %s',
                (producto_id,)
            )
            row = cursor.fetchone()
            return self._row_to_producto(row) if row else None
        finally:
            conn.close()
    
    def obtener_todos_productos(self) -> List[Producto]:
        """
        Obtener todos los productos
        
        Returns:
            Lista de productos
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT id, nombre, stock, costo_unitario, margen_porcentaje, precio_sugerido '
                'FROM productos ORDER BY nombre'
            )
            rows = cursor.fetchall()
            logger.debug(f"Consultados {len(rows)} productos")
            return [self._row_to_producto(row) for row in rows]
        finally:
            conn.close()
    
    def listar_productos(self) -> List[Producto]:
        """Alias de obtener_todos_productos para compatibilidad"""
        return self.obtener_todos_productos()
    
    def actualizar_margen(self, nombre_producto: str, margen_porcentaje: float) -> bool:
        """
        Actualizar margen y precio sugerido de un producto
        
        Args:
            nombre_producto: Nombre del producto
            margen_porcentaje: Porcentaje de margen deseado (0-500%)
        
        Returns:
            True si se actualizó, False si no existe el producto
        
        Raises:
            ErrorValidacionError: Si margen es inválido
            ErrorTransaccionError: Si falla la actualización
        """
        # HARDENING: Validar rango de margen razonable (0-500%)
        if margen_porcentaje < 0:
            raise ErrorValidacionError("margen_porcentaje", margen_porcentaje, "No puede ser negativo")
        
        if margen_porcentaje > 500:
            raise ErrorValidacionError("margen_porcentaje", margen_porcentaje, "Margen excesivo (máximo 500%)")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener producto actual
            cursor.execute(
                'SELECT costo_unitario FROM productos WHERE nombre = ?',
                (nombre_producto,)
            )
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"Producto no encontrado para actualizar margen: {nombre_producto}")
                return False
            
            costo = row[0]
            precio_sugerido = costo * (1 + margen_porcentaje / 100) if costo > 0 else 0
            
            cursor.execute(
                'UPDATE productos SET margen_porcentaje = ?, precio_sugerido = ? WHERE nombre = ?',
                (margen_porcentaje, precio_sugerido, nombre_producto)
            )
            conn.commit()
            logger.info(f"Margen actualizado: {nombre_producto} -> {margen_porcentaje}%")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar margen de {nombre_producto}: {str(e)}")
            raise ErrorTransaccionError("actualizar_margen", str(e))
        finally:
            conn.close()
    
    def actualizar_producto(
        self,
        producto_id: int,
        nombre: str,
        stock: int,
        costo_unitario: float,
        margen_porcentaje: float,
        precio_sugerido: float
    ) -> bool:
        """
        Actualizar todos los campos de un producto
        
        Args:
            producto_id: ID del producto
            nombre: Nombre del producto
            stock: Stock actual
            costo_unitario: Costo unitario
            margen_porcentaje: Porcentaje de margen
            precio_sugerido: Precio de venta sugerido
        
        Returns:
            True si se actualizó exitosamente
        
        Raises:
            ErrorValidacionError: Si los datos son inválidos
            ErrorTransaccionError: Si falla la actualización
        """
        if costo_unitario < 0:
            raise ErrorValidacionError("costo_unitario", costo_unitario, "No puede ser negativo")
        
        if precio_sugerido < 0:
            raise ErrorValidacionError("precio_sugerido", precio_sugerido, "No puede ser negativo")
        
        if margen_porcentaje < 0 or margen_porcentaje > 500:
            raise ErrorValidacionError("margen_porcentaje", margen_porcentaje, "Debe estar entre 0 y 500%")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE productos 
                SET nombre = %s, stock = %s, costo_unitario = %s, margen_porcentaje = %s, precio_sugerido = %s
                WHERE id = %s
            ''', (nombre, stock, costo_unitario, margen_porcentaje, precio_sugerido, producto_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Producto actualizado: {nombre} (ID: {producto_id})")
                return True
            else:
                logger.warning(f"Producto no encontrado para actualizar (ID: {producto_id})")
                return False
                
        except Exception as e:
            logger.error(f"Error al actualizar producto {producto_id}: {str(e)}")
            raise ErrorTransaccionError("actualizar_producto", str(e))
        finally:
            conn.close()
    
    def inicializar_productos(self) -> None:
        """
        Inicializar productos por defecto
        """
        logger.info("Inicializando productos por defecto...")
        for nombre in PRODUCTOS_INICIALES:
            self.crear_producto(nombre)
        logger.info(f"Productos inicializados: {len(PRODUCTOS_INICIALES)}")
    
    def eliminar_producto(self, producto_id: int) -> Tuple[bool, str]:
        """
        Eliminar un producto si no tiene ventas ni compras asociadas
        
        Args:
            producto_id: ID del producto a eliminar
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        
        Raises:
            ErrorValidacionError: Si el producto tiene transacciones asociadas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar que el producto existe
            cursor.execute('SELECT nombre FROM productos WHERE id = %s', (producto_id,))
            row = cursor.fetchone()
            
            if not row:
                return False, "Producto no encontrado"
            
            nombre_producto = row[0]
            
            # Verificar si tiene ventas asociadas
            cursor.execute('SELECT COUNT(*) FROM ventas WHERE producto_id = ?', (producto_id,))
            count_ventas = cursor.fetchone()[0]
            
            if count_ventas > 0:
                return False, f"No se puede eliminar: tiene {count_ventas} venta(s) asociada(s)"
            
            # Verificar si tiene compras asociadas
            cursor.execute('SELECT COUNT(*) FROM compras WHERE producto_id = ?', (producto_id,))
            count_compras = cursor.fetchone()[0]
            
            if count_compras > 0:
                return False, f"No se puede eliminar: tiene {count_compras} compra(s) asociada(s)"
            
            # Eliminar el producto
            cursor.execute('DELETE FROM productos WHERE id = %s', (producto_id,))
            conn.commit()
            
            logger.info(f"Producto eliminado: {nombre_producto} (ID: {producto_id})")
            return True, f"Producto '{nombre_producto}' eliminado correctamente"
            
        except Exception as e:
            logger.error(f"Error al eliminar producto {producto_id}: {str(e)}")
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    @staticmethod
    def _row_to_producto(row) -> Producto:
        """Convertir fila de base de datos a objeto Producto"""
        return Producto(
            id=row[0],
            nombre=row[1],
            stock=row[2],
            costo_unitario=row[3],
            margen_porcentaje=row[4],
            precio_sugerido=row[5]
        )


# =============================================================================
# Funciones wrapper para compatibilidad con Desktop (legacy)
# TODO: Migrar Desktop a usar ProductosService() directamente
# =============================================================================

def obtener_todos_productos() -> list:
    """
    DEPRECATED: Tkinter desktop support removed (2026-02-13)
    Wrapper function maintained for backward compatibility
    
    Returns:
        Lista de diccionarios con datos de productos
    """
    productos_service = ProductosService()
    productos = productos_service.obtener_todos_productos()
    
    # Convertir objetos Producto a diccionarios
    return [
        {
            'id': p.id,
            'nombre': p.nombre,
            'stock': p.stock,
            'precio_compra': p.costo_unitario,
            'precio_venta': p.precio_sugerido,
            'margen': p.margen_porcentaje
        }
        for p in productos
    ]


def obtener_producto_por_id(producto_id: int):
    """
    DEPRECATED: Tkinter desktop support removed (2026-02-13)
    Wrapper function maintained for backward compatibility
    
    Args:
        producto_id: ID del producto
    
    Returns:
        Diccionario con datos del producto o None
    """
    productos_service = ProductosService()
    producto = productos_service.obtener_producto_por_id(producto_id)
    
    if not producto:
        return None
    
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'stock': producto.stock,
        'precio_compra': producto.costo_unitario,
        'precio_venta': producto.precio_sugerido,
        'margen': producto.margen_porcentaje
    }
