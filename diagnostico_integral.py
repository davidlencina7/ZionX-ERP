import os
import sys
import importlib
import subprocess
from pathlib import Path

REQUIRED_FILES = [
    '.env',
    '.env.production',
    'requirements.txt',
    'run_web.py',
    'backend/core/version.py',
    'diagnostico_semaforo.py',
]
REQUIRED_DIRS = [
    'backend',
    'frontend',
    'data',
    'static',
]
REQUIRED_MODULES = [
    'flask',
    'flask_login',
    'flask_wtf',
    'sqlalchemy',
    'psycopg2',
    'dotenv',
]


def check_files():
    print('== Verificando archivos requeridos ==')
    for f in REQUIRED_FILES:
        if not Path(f).exists():
            print(f'  ❌ Falta archivo: {f}')
        else:
            print(f'  ✔ Archivo presente: {f}')

def check_dirs():
    print('== Verificando carpetas requeridas ==')
    for d in REQUIRED_DIRS:
        if not Path(d).exists():
            print(f'  ❌ Falta carpeta: {d}')
        else:
            print(f'  ✔ Carpeta presente: {d}')

def check_modules():
    print('== Verificando módulos de Python ==')
    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
            print(f'  ✔ Módulo importable: {mod}')
        except ImportError:
            print(f'  ❌ Falta módulo: {mod}')

def check_venv():
    print('== Verificando entorno virtual (.venv) ==')
    if not Path('.venv').exists():
        print('  ❌ Falta la carpeta .venv')
    elif not Path('.venv/Scripts/activate').exists() and not Path('.venv/bin/activate').exists():
        print('  ❌ .venv presente pero sin scripts de activación')
    else:
        print('  ✔ Entorno virtual detectado')

def check_pg_dump():
    print('== Verificando pg_dump en PATH ==')
    result = subprocess.run(['where', 'pg_dump'], capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        print(f'  ✔ pg_dump detectado: {result.stdout.strip()}')
    else:
        print('  ❌ pg_dump no encontrado en PATH')

def main():
    print('==== DIAGNÓSTICO INTEGRAL DE ARRANQUE ====')
    print('==== DIAGNÓSTICO INTEGRAL DE ARRANQUE ====')
    check_files()
    print()
    check_dirs()
    print()
    check_venv()
    print()
    check_modules()
    print()
    check_pg_dump()
    print('\n==== Fin del diagnóstico integral ====' )
    print('\nAhora ejecuta: python diagnostico_semaforo.py')

if __name__ == '__main__':
    main()
