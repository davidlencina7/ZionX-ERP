@echo off
REM Script para activar el entorno virtual y arrancar el servidor de producción
cd /d "%~dp0.."
call .venv\Scripts\activate.bat
python tools\prod\prod_server.py
pause
