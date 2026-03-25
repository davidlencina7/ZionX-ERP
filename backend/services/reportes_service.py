"""
Servicio de generación de reportes
Lógica de negocio para análisis y reportes
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from backend.database.connection import DatabaseConnection
from backend.services.productos_service import ProductosService
from backend.services.ventas_service import VentasService

logger = logging.getLogger(__name__)


class ReportesService:
    """Servicio para generar reportes del sistema"""
    
    def __init__(self) -> None:
        self.db = DatabaseConnection.get_instance()
        self.productos_service = ProductosService()
        self.ventas_service = VentasService()
        logger.debug("ReportesService inicializado")
    
    def generar_reporte_diario(self) -> Dict:
        """
        Generar reporte diario del sistema
        
        Returns:
            Dict con información del día actual
        """
        hoy = datetime.now().date()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Ventas del día
            cursor.execute(
                '''SELECT SUM(cantidad) as total_cantidad, 
                   SUM(ganancia_unitaria * cantidad) as ganancia_total
                   FROM ventas
                   WHERE DATE(fecha) = %s''',
                (hoy,)
            )
            venta_dia = cursor.fetchone()
            
            # Compras del día
            cursor.execute(
                '''SELECT SUM(cantidad) as total_cantidad, 
                   SUM(cantidad * costo_unitario) as costo_total
                   FROM compras
                   WHERE DATE(fecha) = %s''',
                (hoy,)
            )
            compra_dia = cursor.fetchone()
            
            # Stock total
            cursor.execute('SELECT SUM(stock) FROM productos')
            stock_total = cursor.fetchone()[0] or 0
            
            # Stock actual de cada producto
            cursor.execute(
                'SELECT nombre, stock, costo_unitario, precio_sugerido FROM productos ORDER BY nombre'
            )
            colnames = [desc[0] for desc in cursor.description]
            productos = [dict(zip(colnames, row)) for row in cursor.fetchall()]
            
            reporte = {
                'fecha': str(hoy),
                'ventas_cantidad': venta_dia[0] or 0,
                'ganancia_total': round(venta_dia[1] or 0, 2),
                'compras_cantidad': compra_dia[0] or 0,
                'compras_costo': round(compra_dia[1] or 0, 2),
                'stock_total': stock_total,
                'productos': productos,
                'ganancia_acumulada': self.ventas_service.calcular_ganancia_total_sistema()
            }
            
            logger.info(f"Reporte diario generado para {hoy}")
            return reporte
        
        finally:
            conn.close()
    
    def generar_reporte_periodo(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> Dict:
        """
        Generar reporte para un período específico
        
        Args:
            fecha_inicio: Fecha inicial del período
            fecha_fin: Fecha final del período
        
        Returns:
            Dict con resumen del período
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Ventas del período
            cursor.execute(
                '''SELECT SUM(cantidad) as total_cantidad, 
                   SUM(ganancia_unitaria * cantidad) as ganancia_total
                   FROM ventas
                   WHERE fecha BETWEEN ? AND ?''',
                (fecha_inicio, fecha_fin)
            )
            venta_periodo = cursor.fetchone()
            
            # Compras del período
            cursor.execute(
                '''SELECT SUM(cantidad) as total_cantidad, 
                   SUM(cantidad * costo_unitario) as costo_total
                   FROM compras
                   WHERE fecha BETWEEN ? AND ?''',
                (fecha_inicio, fecha_fin)
            )
            compra_periodo = cursor.fetchone()
            
            reporte = {
                'periodo_inicio': str(fecha_inicio),
                'periodo_fin': str(fecha_fin),
                'ventas_cantidad': venta_periodo[0] or 0,
                'ganancia_total': round(venta_periodo[1] or 0, 2),
                'compras_cantidad': compra_periodo[0] or 0,
                'compras_costo': round(compra_periodo[1] or 0, 2)
            }
            
            logger.info(f"Reporte de período generado: {fecha_inicio} a {fecha_fin}")
            return reporte
        
        finally:
            conn.close()
    
    def obtener_productos_bajo_stock(self, limite: int = 5) -> List[Dict]:
        """
        Obtener productos con stock bajo
        
        Args:
            limite: Límite de stock a considerar como bajo
        
        Returns:
            Lista de productos con stock bajo
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT id, nombre, stock FROM productos WHERE stock > 0 AND stock <= ? ORDER BY stock ASC',
                (limite,)
            )
            colnames = [desc[0] for desc in cursor.description]
            productos = [dict(zip(colnames, row)) for row in cursor.fetchall()]
            logger.debug(f"Consultados {len(productos)} productos con stock bajo")
            return productos
        finally:
            conn.close()
    
    def obtener_productos_mas_vendidos(self, limite: int = 10) -> List[Dict]:
        """
        Obtener productos más vendidos
        
        Args:
            limite: Número máximo de productos a retornar
        
        Returns:
            Lista de productos ordenados por cantidad vendida
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''SELECT productos.nombre, SUM(ventas.cantidad) as total_vendido,
                   SUM(ventas.ganancia_unitaria * ventas.cantidad) as ganancia_total
                   FROM ventas
                   JOIN productos ON ventas.producto_id = productos.id
                   GROUP BY productos.id
                   ORDER BY total_vendido DESC
                   LIMIT ?''',
                (limite,)
            )
            colnames = [desc[0] for desc in cursor.description]
            productos = [dict(zip(colnames, row)) for row in cursor.fetchall()]
            logger.debug(f"Consultados {len(productos)} productos más vendidos")
            return productos
        finally:
            conn.close()

