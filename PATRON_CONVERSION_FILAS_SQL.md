# Patrón seguro para convertir filas de base de datos a diccionario (PostgreSQL y SQLite)

Cuando se trabaja con diferentes motores de base de datos (SQLite, PostgreSQL, etc.), la conversión de filas a diccionarios puede variar:

- **SQLite**: `dict(row)` funciona si el cursor devuelve objetos tipo Row.
- **PostgreSQL (psycopg2)**: el cursor devuelve tuplas, por lo que `dict(row)` falla si la tupla tiene más de 2 elementos.

## Patrón recomendado (compatible con ambos)

```python
colnames = [desc[0] for desc in cursor.description]
resultados = [dict(zip(colnames, row)) for row in cursor.fetchall()]
```

- Esto asegura que cada fila se convierte correctamente en un diccionario, sin importar el motor de base de datos.
- Úsalo siempre que necesites listas de diccionarios a partir de resultados SQL.

## Ejemplo completo
```python
cursor.execute('SELECT id, nombre, stock FROM productos')
colnames = [desc[0] for desc in cursor.description]
productos = [dict(zip(colnames, row)) for row in cursor.fetchall()]
```

## Beneficios
- Evita errores como: `dictionary update sequence element #0 has length N; 2 is required`.
- Código portable y robusto para migraciones entre SQLite y PostgreSQL.

---

> **Recomendación:** Aplica este patrón en todos los servicios y utilidades que conviertan filas SQL a diccionarios.
