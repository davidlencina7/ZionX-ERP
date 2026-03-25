"""
Blueprint de Sistema - Funciones administrativas y mantenimiento
"""
from flask import Blueprint, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from io import BytesIO
import zipfile
import shutil
from pathlib import Path

from backend.config.settings import BASE_DIR
from backend.utils.backup import backup_database

sistema_bp = Blueprint('sistema', __name__)


@sistema_bp.route('/backup/descargar', methods=['GET'])
@login_required
def descargar_backup():
    """Crear y descargar backup de la base de datos"""
    try:
        # Crear backup temporal
        backup_path = backup_database()
        
        # Crear archivo ZIP en memoria
        memory_file = BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Agregar la base de datos
            zf.write(backup_path, Path(backup_path).name)
            
            # Agregar información adicional
            info_content = f"""BACKUP PIU PIU ERP
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Usuario: {current_user.nombre_usuario}
Base de datos: PostgreSQL

Este archivo contiene una copia completa de la base de datos.
Para restaurar, use el backup de PostgreSQL correspondiente.
"""
            zf.writestr('README.txt', info_content)
        
        memory_file.seek(0)
        
        # Nombre del archivo
        filename = f"backup_piupiu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        # Eliminar backup temporal
        try:
            Path(backup_path).unlink()
        except:
            pass
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error al crear backup: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))


@sistema_bp.route('/backup/listar', methods=['GET'])
@login_required
def listar_backups():
    """Listar backups disponibles"""
    try:
        backup_dir = BASE_DIR / 'backups'
        
        if not backup_dir.exists():
            backups = []
        else:
            backups = []
            for file in backup_dir.glob('*.db'):
                stat = file.stat()
                backups.append({
                    'nombre': file.name,
                    'ruta': str(file),
                    'tamano': stat.st_size,
                    'fecha': datetime.fromtimestamp(stat.st_mtime)
                })
            
            # Ordenar por fecha descendente
            backups.sort(key=lambda x: x['fecha'], reverse=True)
        
        return {
            'success': True,
            'backups': backups,
            'total': len(backups)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
