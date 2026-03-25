"""
Servicio de panel gerencial
Separa la logica de calculo del controlador web
"""
import logging
from datetime import date
from typing import Dict, List

from backend.services.ventas_service import VentasService
from backend.services.compras_service import ComprasService
from backend.services.productos_service import ProductosService
from backend.services.gastos_service import GastosService

logger = logging.getLogger(__name__)


class GerencialService:
    """Servicio para construir los datos del panel gerencial"""

    def __init__(self) -> None:
        self.ventas_service = VentasService()
        self.compras_service = ComprasService()
        self.productos_service = ProductosService()
        self.gastos_service = GastosService()
        logger.debug("GerencialService inicializado")

    def construir_panel_data(self, fecha_ref: date | None = None) -> Dict:
        """
        Construir el dataset del panel gerencial

        Args:
            fecha_ref: Fecha base para calcular dia y mes (por defecto hoy)

        Returns:
            Dict con todas las variables requeridas por el template
        """
        if fecha_ref is None:
            fecha_ref = date.today()

        # Diccionario de meses en espanol
        mes_nombre = {
            '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
            '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
            '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
        }

        ventas = self.ventas_service.listar_ventas()
        compras = self.compras_service.listar_compras()
        productos = self.productos_service.listar_productos()
        gastos = self.gastos_service.listar_gastos()
        
        logger.debug(f"[GERENCIAL] Datos cargados: {len(ventas)} ventas, {len(compras)} compras, {len(productos)} productos, {len(gastos)} gastos")

        # Fecha de referencia
        hoy = fecha_ref.strftime('%d/%m/%Y')
        fecha_filtro = fecha_ref.strftime('%Y-%m-%d')

        # 1. Ganancia bruta (total acumulado)
        ganancia_bruta = sum([float(v.ganancia_unitaria) * float(v.cantidad) for v in ventas])
        logger.debug(f"[GERENCIAL] Ganancia bruta calculada: ${ganancia_bruta:.2f}")
        if ventas:
            logger.debug(f"[GERENCIAL] Primera venta: ganancia_unitaria={ventas[0].ganancia_unitaria}, cantidad={ventas[0].cantidad}")

        # 2. Stock valorizado
        stock_valorizado = sum([float(p.stock) * float(p.costo_unitario) for p in productos])
        logger.debug(f"[GERENCIAL] Stock valorizado calculado: ${stock_valorizado:.2f}")
        if productos:
            logger.debug(f"[GERENCIAL] Primer producto: stock={productos[0].stock}, costo_unitario={productos[0].costo_unitario}")

        # 3. Caja actual (ventas - compras - gastos)
        total_ventas = sum([float(v.precio_unitario) * float(v.cantidad) for v in ventas])
        total_compras = sum([float(c.costo_unitario) * float(c.cantidad) for c in compras])
        total_gastos = sum([float(g.monto) for g in gastos])
        caja_actual = total_ventas - total_compras - total_gastos

        # 4. Resultado acumulado
        resultado_acumulado = ganancia_bruta - total_gastos

        # Datos del dia
        ventas_dia = []
        compras_dia = []

        for v in ventas:
            if hasattr(v.fecha, 'strftime'):
                fecha_str = v.fecha.strftime('%Y-%m-%d')
            else:
                fecha_str = str(v.fecha)[:10] if v.fecha else ''

            if fecha_str == fecha_filtro:
                ventas_dia.append(v)

        for c in compras:
            if hasattr(c.fecha, 'strftime'):
                fecha_str = c.fecha.strftime('%Y-%m-%d')
            else:
                fecha_str = str(c.fecha)[:10] if c.fecha else ''

            if fecha_str == fecha_filtro:
                compras_dia.append(c)

        ventas_dia_cantidad = len(ventas_dia)
        ventas_dia_monto = sum([float(v.precio_unitario) * float(v.cantidad) for v in ventas_dia])
        ventas_dia_ganancia = sum([float(v.ganancia_unitaria) * float(v.cantidad) for v in ventas_dia])

        compras_dia_cantidad = len(compras_dia)
        compras_dia_monto = sum([float(c.costo_unitario) * float(c.cantidad) for c in compras_dia])

        balance_dia = ventas_dia_monto - compras_dia_monto

        # Datos del mes actual
        mes_actual = fecha_ref.strftime('%Y-%m')
        mes_texto = f"{mes_nombre[mes_actual.split('-')[1]]} {mes_actual.split('-')[0]}"

        ventas_mes = []
        compras_mes = []

        for v in ventas:
            if hasattr(v.fecha, 'strftime'):
                mes_str = v.fecha.strftime('%Y-%m')
            else:
                mes_str = str(v.fecha)[:7] if v.fecha else ''

            if mes_str == mes_actual:
                ventas_mes.append(v)

        for c in compras:
            if hasattr(c.fecha, 'strftime'):
                mes_str = c.fecha.strftime('%Y-%m')
            else:
                mes_str = str(c.fecha)[:7] if c.fecha else ''

            if mes_str == mes_actual:
                compras_mes.append(c)

        # Enriquecer ventas y compras con nombre de producto
        productos_dict = {p.id: p.nombre for p in productos}

        ventas_mes_detalle = []
        for v in ventas_mes:
            ventas_mes_detalle.append({
                'id': v.id,
                'producto': productos_dict.get(v.producto_id, 'Desconocido'),
                'producto_id': v.producto_id,
                'cantidad': float(v.cantidad),
                'precio_unitario': float(v.precio_unitario),
                'total': float(v.precio_unitario) * float(v.cantidad),
                'ganancia': float(v.ganancia_unitaria) * float(v.cantidad),
                'fecha': v.fecha
            })

        compras_mes_detalle = []
        for c in compras_mes:
            compras_mes_detalle.append({
                'id': c.id,
                'producto': productos_dict.get(c.producto_id, 'Desconocido'),
                'producto_id': c.producto_id,
                'cantidad': float(c.cantidad),
                'costo_unitario': float(c.costo_unitario),
                'total': float(c.costo_unitario) * float(c.cantidad),
                'fecha': c.fecha
            })

        # Ventas por producto
        ventas_por_producto = []
        for producto in productos:
            ventas_producto = [v for v in ventas if v.producto_id == producto.id]
            if ventas_producto:
                cantidad_vendida = sum([float(v.cantidad) for v in ventas_producto])
                ingresos = sum([float(v.precio_unitario) * float(v.cantidad) for v in ventas_producto])
                ganancia = sum([float(v.ganancia_unitaria) * float(v.cantidad) for v in ventas_producto])
                margen = (ganancia / ingresos * 100) if ingresos > 0 else 0

                ventas_por_producto.append({
                    'nombre': producto.nombre,
                    'cantidad': cantidad_vendida,
                    'ingresos': ingresos,
                    'ganancia': ganancia,
                    'margen': margen
                })

        ventas_por_producto.sort(key=lambda x: x['ganancia'], reverse=True)

        # Costo promedio actualizado
        productos_costo = []
        for producto in productos:
            precio_venta = (
                float(producto.precio_venta)
                if hasattr(producto, 'precio_venta')
                else float(producto.costo_unitario) * 1.3
            )
            margen_unitario = float(precio_venta) - float(producto.costo_unitario)
            valor_stock = float(producto.stock) * float(producto.costo_unitario)

            productos_costo.append({
                'nombre': producto.nombre,
                'stock': float(producto.stock),
                'costo_promedio': float(producto.costo_unitario),
                'precio_venta': float(precio_venta),
                'margen_unitario': float(margen_unitario),
                'valor_stock': float(valor_stock)
            })

        return {
            'ganancia_bruta': ganancia_bruta,
            'stock_valorizado': stock_valorizado,
            'resultado_acumulado': resultado_acumulado,
            'caja_actual': caja_actual,
            'fecha_hoy': hoy,
            'ventas_dia_cantidad': ventas_dia_cantidad,
            'ventas_dia_monto': ventas_dia_monto,
            'ventas_dia_ganancia': ventas_dia_ganancia,
            'compras_dia_cantidad': compras_dia_cantidad,
            'compras_dia_monto': compras_dia_monto,
            'balance_dia': balance_dia,
            'ventas_por_producto': ventas_por_producto,
            'productos_costo': productos_costo,
            'ventas_mes': ventas_mes_detalle,
            'compras_mes': compras_mes_detalle,
            'mes_actual': mes_texto
        }
