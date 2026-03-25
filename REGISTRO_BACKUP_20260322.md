# Registro de Backup de Base de Datos

**Fecha de respaldo:** 22 de marzo de 2026  
**Hora:** 19:16:24  
**Responsable:** Proceso automatizado (scripts/backup_automatizado.py)

## Archivo generado
- **Ruta:** `data/backups/backup_20260322_191624.sql`
- **Formato:** PostgreSQL personalizado (pg_dump -F c)
- **Incluye:** Estructura, datos, funciones, triggers, políticas RLS, privilegios y objetos relacionados.

## Comando utilizado
```sh
pg_dump -h aws-1-sa-east-1.pooler.supabase.com -p 5432 -U postgres.doumluosutxyysitnnqb -F c -b -v -f "data/backups/backup_20260322_191624.sql" postgres
```

## Credenciales utilizadas
- **Usuario:** postgres.doumluosutxyysitnnqb
- **Contraseña:** BtLcQB5pI3XV4dR7
- **Host:** aws-1-sa-east-1.pooler.supabase.com
- **Puerto:** 5432
- **Base de datos:** postgres

## Procedimiento correcto para realizar el backup
1. **Ubícate en la raíz del proyecto:**
	```sh
	cd "D:/programas vs code/ZionX ERP"
	```
2. **Establece la variable de entorno (PowerShell):**
	```powershell
	$env:DATABASE_URL="postgresql://postgres.doumluosutxyysitnnqb:BtLcQB5pI3XV4dR7@aws-1-sa-east-1.pooler.supabase.com:5432/postgres"
	```
3. **Ejecuta el script de backup:**
	```sh
	python scripts/backup_automatizado.py
	```
	El script generará el archivo de respaldo en la carpeta `data/backups/` con un nombre que incluye la fecha y hora.

### Alternativa: Comando manual directo
Si prefieres hacer el backup manualmente, ejecuta:
```sh
PGPASSWORD=BtLcQB5pI3XV4dR7 pg_dump -h aws-1-sa-east-1.pooler.supabase.com -p 5432 -U postgres.doumluosutxyysitnnqb -F c -b -v -f "backup_zionx_20260322.dump" postgres
```
En PowerShell:
```powershell
$env:PGPASSWORD="BtLcQB5pI3XV4dR7"
pg_dump -h aws-1-sa-east-1.pooler.supabase.com -p 5432 -U postgres.doumluosutxyysitnnqb -F c -b -v -f "backup_zionx_20260322.dump" postgres
```

## Restauración del backup
Para restaurar el backup en otra base de datos:
```sh
pg_restore -h <host> -p <puerto> -U <usuario> -d <nombre_base_destino> -v "ruta/del/backup.dump"
```
Ejemplo concreto:
```sh
PGPASSWORD=BtLcQB5pI3XV4dR7 pg_restore -h aws-1-sa-east-1.pooler.supabase.com -p 5432 -U postgres.doumluosutxyysitnnqb -d postgres -v "data/backups/backup_20260322_191624.sql"
```

## Notas
- El backup fue realizado exitosamente y verificado en consola.
- El archivo puede ser restaurado con `pg_restore`.
- Se recomienda almacenar este archivo en un lugar seguro y realizar backups periódicos.
- Las credenciales aquí documentadas corresponden al entorno de Supabase al 22/03/2026.

---

_Archivo generado automáticamente por GitHub Copilot (GPT-4.1) a solicitud del usuario._
