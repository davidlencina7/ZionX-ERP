from datetime import datetime

 # Eliminado: solo PostgreSQL

productos = c.execute('SELECT id, nombre, stock, costo_unitario FROM productos').fetchall()

for p in productos:
    producto_id, nombre, stock, costo_unitario = p
    print(f'Producto: {nombre}, Stock antes: {stock}')
    if stock > 0:
        precio_unitario = 5000
        ganancia_unitaria = precio_unitario - costo_unitario
        cantidad = 1
        forma_pago = 'efectivo'
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        print(f'Producto: {nombre}, sin stock disponible')

