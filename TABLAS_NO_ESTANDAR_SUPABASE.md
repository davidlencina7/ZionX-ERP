# Tablas no estándar detectadas en PostgreSQL (Supabase)

Fecha de revisión: 22/03/2026

Estas tablas existen en la base de datos pero **no forman parte del núcleo estándar de ZionX ERP**. No se recomienda eliminarlas sin antes revisar si alguna lógica personalizada, migración o integración depende de ellas.

- **activos_fijos**: Tabla auxiliar, no estándar. Verificar si hay lógica personalizada antes de eliminar.
- **alembic_version**: Usada por herramientas de migración automática (Alembic). Eliminar solo si no usas migraciones automáticas.
- **sync_log**: Tabla de logs de sincronización. Eliminar solo si no tienes procesos de sincronización personalizados.

**Recomendación:**
- Mantener documentadas estas tablas.
- Si en el futuro decides que no son necesarias y confirmas que no hay dependencias, puedes eliminarlas con seguridad usando `DROP TABLE`.

---

**Tablas clave que NO debes eliminar:**
productos, compras, ventas, usuarios, gastos, activos, accounts, journal_entries, journal_lines, inventory_movements, plan_cuentas, asientos_contables, lineas_asiento, movimientos_contables, operaciones

---

Este archivo es solo para referencia y control de limpieza de la base de datos.
