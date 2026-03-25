@echo off
REM Script robusto para activar entorno virtual y arrancar el servidor
cd /d "%~dp0"
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Entorno virtual activado.
) else (
    echo ERROR: No se encontró el entorno virtual .venv
    pause
    exit /b 1
)
echo Iniciando servidor...
python start_web.py
pause