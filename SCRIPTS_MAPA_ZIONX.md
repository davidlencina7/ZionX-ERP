# Mapeo de scripts y automatizaciones ZionX ERP (marzo 2026)

## Scripts Python principales

- run_web.py
- start_web.py
- verificar_estructura_db.py
- validar_pg_dump.py
- buscar_pg_dump.py
- find_database_path.py
- test_db.py

### Automatización y backup
- scripts/backup_automatizado.py

### Herramientas de entorno y pruebas
- tools/tests/manual/test_entorno.py

### Backend (core y utilidades)
- backend/core/app_factory.py
- backend/utils/backup.py

### Controladores de diagnóstico
- backend/controllers/diagnostico_history.py
- backend/controllers/diagnostico_scheduler.py
- backend/controllers/diagnostico_plugins.py

### Herramientas de desarrollo
- tools/dev/dev_server.py
- tools/dev/crear_usuario_admin.py
- tools/dev/crear_usuario_ilencina.py
- tools/dev/verificar_usuario_ilencina.py
- tools/dev/simulacro_venta.py
- tools/dev/simulacro_venta_todos.py
- tools/dev/reset_db_for_restore.py
- tools/dev/reset_db_for_restore_extra.py
- tools/dev/reset_db_for_restore_final.py
- tools/dev/reset_ilencina_backend.py
- tools/dev/insert_ilencina.py
- tools/dev/borrar_usuarios_postgres.py
- tools/dev/borrar_usuarios_postgres_con_dependencias.py

## Scripts por lotes (Windows BAT)
- automatizar_puesta_en_marcha.bat
- arrancar_server_produccion.bat
- arrancar_server_prod.bat

## Otros archivos relevantes
- requirements.txt
- ORGANIZACION_SISTEMA.md
- db_password.txt

---

Este archivo mapea los scripts y automatizaciones clave del sistema ZionX ERP, agrupados por función y carpeta. Incluye scripts de diagnóstico, automatización, backup, pruebas, utilidades y arranque, siguiendo la estructura real del proyecto.

> Actualizado: 21 de marzo de 2026
