@echo off
REM Script de arranque robusto ZionX ERP - Producción

REM Activar entorno virtual
cd /d "D:\programas vs code\ZionX ERP"
call .venv\Scripts\activate.bat

REM Diagnóstico previo
python tools\diagnostico_sincronizacion_areas.py

REM Arranque robusto del servidor
call arrancar_server_robusto.bat

pause
