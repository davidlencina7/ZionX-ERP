import subprocess
import sys
import os
from datetime import datetime

# Configuración de pruebas
PRUEBAS = [
    {
        'nombre': 'Conexión a PostgreSQL',
        'comando': [sys.executable, 'test_db.py'],
        'critico': True
    },
    {
        'nombre': 'Arranque del servidor producción',
        'comando': ['cmd', '/c', 'call .venv\\Scripts\\activate.bat && python tools/prod/prod_server.py'],
        'critico': True
    },
    {
        'nombre': 'Verificación usuario ilencina',
        'comando': [sys.executable, 'tools/dev/verificar_usuario_ilencina.py'],
        'critico': False
    },
    {
        'nombre': 'Backup con pg_dump',
        'comando': [sys.executable, 'backend/utils/backup.py'],
        'critico': False
    },
]

RESULTADOS = []

print('--- SEMÁFORO DE PRUEBAS AUTOMATIZADAS ---')
print(f'Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

exitos = 0

for prueba in PRUEBAS:
    print(f"Prueba: {prueba['nombre']}")
    if prueba['nombre'] == 'Arranque del servidor producción' and os.name == 'nt':
        print('⚠️  ADVERTENCIA: En Windows, el arranque de producción debe hacerse SIEMPRE desde una terminal con el entorno virtual activado manualmente (activate.bat o Activate.ps1).')
        print('    Ejemplo:')
        print('        .venv\\Scripts\\activate')
        print('        python tools/prod/prod_server.py')
        print('    O usa el script arrancar_server_produccion.bat desde CMD.')
        RESULTADOS.append({'nombre': prueba['nombre'], 'estado': 'ADVERTENCIA', 'critico': prueba['critico'], 'detalle': 'Requiere activación manual del entorno virtual.'})
        print()
        continue
    try:
        resultado = subprocess.run(prueba['comando'], capture_output=True, text=True, timeout=30)
        if resultado.returncode == 0:
            print('🟢 OK')
            exitos += 1
            RESULTADOS.append({'nombre': prueba['nombre'], 'estado': 'OK', 'critico': prueba['critico']})
        else:
            print('🔴 ERROR')
            print(resultado.stderr or resultado.stdout)
            RESULTADOS.append({'nombre': prueba['nombre'], 'estado': 'ERROR', 'critico': prueba['critico'], 'detalle': resultado.stderr or resultado.stdout})
    except Exception as e:
        print('🔴 ERROR')
        print(str(e))
        RESULTADOS.append({'nombre': prueba['nombre'], 'estado': 'ERROR', 'critico': prueba['critico'], 'detalle': str(e)})
    print()

avance = int((exitos / len(PRUEBAS)) * 100)
print(f'Progreso total: {avance}%')

# Lista de corrección post diagnóstico
pendientes = [r['nombre'] for r in RESULTADOS if r['estado'] == 'ERROR']
if pendientes:
    print('\n--- Lista de corrección post diagnóstico ---')
    for i, p in enumerate(pendientes, 1):
        print(f'{i}. {p}')
else:
    print('\n¡Todos los tests pasaron correctamente!')
