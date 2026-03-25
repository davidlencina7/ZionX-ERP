@echo off
REM Script para automatizar puesta en marcha de ZionX ERP

REM 1. Activar entorno virtual
call .venv\Scripts\activate.bat

REM 2. Instalar dependencias
pip install -r requirements.txt

REM 3. Copiar .env.production a .env si no existe
if not exist .env copy .env.production .env

REM 4. Ejecutar servidor en producción
python tools\prod\prod_server.py
