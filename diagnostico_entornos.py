# --- IMPORTS AL INICIO ---
import os
import sys
import platform
import pkg_resources
import datetime
import traceback
import json

def get_env_vars():
    keys = [
        'FLASK_ENV', 'FLASK_DEBUG', 'DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_KEY',
        'PYTHONPATH', 'PATH', 'VIRTUAL_ENV', 'ENV', 'APP_SETTINGS', 'SECRET_KEY'
    ]
    return {k: os.environ.get(k, None) for k in keys}

def get_python_info():
    return {
        'python_version': sys.version,
        'executable': sys.executable,
        'platform': platform.platform(),
        'cwd': os.getcwd(),
    }

def get_installed_packages():
    try:
        return sorted([f"{d.project_name}=={d.version}" for d in pkg_resources.working_set])
    except Exception as e:
        return [f"Error obteniendo paquetes: {e}"]

def check_db_connection():
    try:
        import psycopg2
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return 'DATABASE_URL no definida'
        conn = psycopg2.connect(db_url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute('SELECT NOW();')
        now = cur.fetchone()
        cur.close()
        conn.close()
        return f'Conexión exitosa. Fecha/hora DB: {now[0]}'
    except Exception as e:
        return f'Error de conexión: {e}\n{traceback.format_exc()}'

def get_flask_config():
    try:
        from flask import current_app
        return {
            'DEBUG': current_app.config.get('DEBUG'),
            'TESTING': current_app.config.get('TESTING'),
            'ENV': current_app.config.get('ENV'),
            'SECRET_KEY': current_app.config.get('SECRET_KEY'),
        }
    except Exception:
        return 'No se pudo acceder a current_app (¿no está en contexto Flask?)'

def check_permissions():
    files = ['.env', 'backend/config/settings.py', 'requirements.txt']
    perms = {}
    for f in files:
        try:
            perms[f] = oct(os.stat(f).st_mode)[-3:]
        except Exception as e:
            perms[f] = f'Error: {e}'
    return perms

def generar_diagnostico_dict():
    return {
        'fecha': str(datetime.datetime.now()),
        'env_vars': get_env_vars(),
        'python_info': get_python_info(),
        'installed_packages': get_installed_packages(),
        'flask_config': get_flask_config(),
        'file_permissions': check_permissions(),
        'db_connection': check_db_connection(),
    }

def guardar_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def cargar_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def comparar_dicts(d1, d2, nombre1='Entorno 1', nombre2='Entorno 2'):
    lines = []
    lines.append(f"Comparación de diagnósticos: {nombre1} vs {nombre2}\n")
    for key in d1:
        if key not in d2:
            lines.append(f"Clave '{key}' solo en {nombre1}")
            continue
        v1 = d1[key]
        v2 = d2[key]
        if v1 == v2:
            continue
        lines.append(f"--- Diferencia en '{key}':")
        if isinstance(v1, list) and isinstance(v2, list):
            set1 = set(v1)
            set2 = set(v2)
            only1 = set1 - set2
            only2 = set2 - set1
            if only1:
                lines.append(f"  Solo en {nombre1}: {sorted(list(only1))}")
            if only2:
                lines.append(f"  Solo en {nombre2}: {sorted(list(only2))}")
        elif isinstance(v1, dict) and isinstance(v2, dict):
            for subk in set(v1.keys()).union(v2.keys()):
                subv1 = v1.get(subk)
                subv2 = v2.get(subk)
                if subv1 != subv2:
                    lines.append(f"  {subk}: {nombre1}={subv1} | {nombre2}={subv2}")
        else:
            lines.append(f"  {nombre1}: {v1}")
            lines.append(f"  {nombre2}: {v2}")
    return '\n'.join(lines)

def main():
    args = sys.argv[1:]
    if len(args) == 2:
        # Modo comparación
        d1 = cargar_json(args[0])
        d2 = cargar_json(args[1])
        nombre1 = os.path.basename(args[0])
        nombre2 = os.path.basename(args[1])
        comparacion = comparar_dicts(d1, d2, nombre1, nombre2)
        out_file = f"reporte_comparacion_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(comparacion)
        print(f"Reporte de comparación generado: {out_file}")
    else:
        # Modo diagnóstico normal
        diagnostico = generar_diagnostico_dict()
        out_file = f"diagnostico_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        guardar_json(diagnostico, out_file)
        print(f"Diagnóstico generado: {out_file}")

if __name__ == '__main__':
    main()
