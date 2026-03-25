@echo off
REM Script robusto para activar entorno virtual, instalar dependencias y arrancar el servidor ZionX ERP
REM Sigue el circuito de arranque documentado en ORGANIZACION_SISTEMA.md

REM 1. Ir a la raíz del proyecto
cd /d "%~dp0"

REM 2. Activar entorno virtual
echo === Activando entorno virtual (.venv) ===
if not exist .venv\Scripts\activate.bat (
	echo [ERROR] No existe el entorno virtual .venv. Ejecute: python -m venv .venv
	pause
	exit /b 1
)
call .venv\Scripts\activate.bat
if not defined VIRTUAL_ENV (
	echo [ERROR] No se pudo activar el entorno virtual. Revise la instalación.
	pause
	exit /b 1
)
echo [OK] Entorno virtual activado.

REM 3. Instalar dependencias si es necesario (opcional, descomentar si se requiere)
REM echo === Instalando dependencias (pip install -r requirements.txt) ===
REM pip install -r requirements.txt

REM 4. Verificar archivo de entorno
if not exist .env.production (
	echo [ERROR] Falta el archivo .env.production. Configure las variables de entorno.
	pause
	exit /b 1
)
echo [OK] Archivo .env.production presente.

REM 5. Validar presencia de pg_dump antes de arrancar el servidor
echo === Validando presencia de pg_dump ===
python validar_pg_dump.py
if errorlevel 1 (
	echo [ERROR] No se puede arrancar el servidor sin pg_dump en el PATH.
	pause
	exit /b 1
)

REM 6. Arrancar el servidor de producción
echo === Iniciando servidor de producción (Waitress) ===
python tools\prod\prod_server.py
if errorlevel 1 (
	echo [ERROR] Falló el arranque del servidor. Revisa los logs y la configuración.
	pause
	exit /b 1
)
echo [OK] Servidor iniciado correctamente.
pause
