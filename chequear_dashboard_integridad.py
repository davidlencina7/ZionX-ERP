import sys
from backend.services.productos_service import ProductosService
from backend.services.ventas_service import VentasService
from backend.services.compras_service import ComprasService

print("[CHECK] Iniciando chequeo de integridad del flujo dashboard\n")

# 1. Chequear productos
productos_service = ProductosService()
todos_productos = productos_service.obtener_todos_productos()
print(f"[CHECK] todos_productos: tipo={type(todos_productos)}, cantidad={len(todos_productos)}")
if len(todos_productos) > 0:
    print(f"[CHECK] tipo primer producto: {type(todos_productos[0])}")
    print(f"[CHECK] primer producto: {todos_productos[0]}")
    for i, p in enumerate(todos_productos):
        if isinstance(p, dict):
            if 'id' not in p or 'nombre' not in p:
                print(f"[ERROR] Producto dict sin id/nombre en posición {i}: {p}")
        else:
            if not hasattr(p, 'id') or not hasattr(p, 'nombre'):
                print(f"[ERROR] Producto objeto sin id/nombre en posición {i}: {p}")

# 2. Chequear construcción de productos_dict
productos_dict = {}
for p in todos_productos:
    try:
        if isinstance(p, dict):
            productos_dict[p.get('id')] = p.get('nombre')
        else:
            productos_dict[p.id] = p.nombre
    except Exception as e:
        print(f"[ERROR] Producto inválido para dict: {p} - {e}")
print(f"[CHECK] productos_dict construido correctamente: {productos_dict}")

# 3. Chequear ventas
ventas_service = VentasService()
todas_ventas = ventas_service.listar_ventas()
print(f"[CHECK] todas_ventas: tipo={type(todas_ventas)}, cantidad={len(todas_ventas)}")
if len(todas_ventas) > 0:
    v = todas_ventas[0]
    print(f"[CHECK] primer venta: {v}")
    if not hasattr(v, 'producto_id') or not hasattr(v, 'fecha'):
        print(f"[ERROR] Venta sin producto_id o fecha: {v}")

# 4. Chequear compras
compras_service = ComprasService()
todas_compras = compras_service.obtener_todas_compras()
print(f"[CHECK] todas_compras: tipo={type(todas_compras)}, cantidad={len(todas_compras)}")
if len(todas_compras) > 0:
    c = todas_compras[0]
    print(f"[CHECK] primera compra: {c}")
    if not hasattr(c, 'producto_id') or not hasattr(c, 'fecha'):
        print(f"[ERROR] Compra sin producto_id o fecha: {c}")

print("\n[CHECK] Chequeo de integridad del flujo dashboard finalizado.")
