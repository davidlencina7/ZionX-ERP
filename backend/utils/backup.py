"""
Servicio de backup de base de datos
Gestión de copias de seguridad de base de datos (solo PostgreSQL)
"""
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


# Asegurar que la raíz del proyecto esté en sys.path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.config.settings import BASE_DIR

logger = logging.getLogger(__name__)


def backup_database(destino: Optional[str] = None) -> str:
    """
    Crear backup de la base de datos PostgreSQL
    
    Args:
        destino: Ruta destino del backup. Si None, crea en carpeta backups/ con timestamp
    
    Returns:
        Ruta del archivo de backup creado
    
    Raises:
        ValueError: Si la base de datos es :memory:
        FileNotFoundError: Si database_path no existe
        IOError: Si falla la copia
    
    Example:
        >>> backup_path = backup_database()
        >>> print(f"Backup creado en: {backup_path}")
    """
    
    
    # Crear carpeta de backups si no existe
    backup_dir = BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)

    # Generar nombre de backup con timestamp
    if destino is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        destino = str(backup_dir / f'piupiu_backup_{timestamp}.sql')

    # Obtener variables de entorno para conexión
    import os
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise RuntimeError('DATABASE_URL no está definida en el entorno.')

    # Parsear la URL para extraer datos de conexión
    import re
    m = re.match(r'postgresql://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/([^?]+)', db_url)
    if not m:
        raise RuntimeError('DATABASE_URL no tiene el formato esperado para PostgreSQL.')
    user, password, host, port, dbname = m.group(1), m.group(2), m.group(3), m.group(4) or '5432', m.group(5)

    # Construir comando pg_dump
    # Nota: pg_dump debe estar en el PATH del sistema
    cmd = [
        'pg_dump',
        f'-h', host,
        f'-p', port,
        f'-U', user,
        '-F', 'c',  # Formato custom
        '-b',       # Incluir blobs
        '-f', destino,
        dbname
    ]

    # Ejecutar pg_dump con la contraseña en el entorno
    import subprocess
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"✗ Error creando backup: {result.stderr}")
            raise IOError(f"Falló la creación del backup: {result.stderr}")
        backup_size = Path(destino).stat().st_size
        logger.info(f"✓ Backup PostgreSQL creado exitosamente: {destino} ({backup_size} bytes)")
        return destino
    except Exception as e:
        logger.error(f"✗ Error creando backup: {str(e)}")
        raise IOError(f"Falló la creación del backup: {str(e)}")


def list_backups() -> list:
    """
    Listar todos los backups disponibles
    
    Returns:
        Lista de tuplas (nombre, fecha_modificacion, tamaño_bytes)
    """
    backup_dir = BASE_DIR / 'backups'
    
    if not backup_dir.exists():
        return []
    
    backups = []
    for backup_file in backup_dir.glob('*.db'):
        stat = backup_file.stat()
        backups.append({
            'nombre': backup_file.name,
            'ruta': str(backup_file),
            'fecha': datetime.fromtimestamp(stat.st_mtime),
            'tamano': stat.st_size
        })
    
    # Ordenar por fecha descendente
    backups.sort(key=lambda x: x['fecha'], reverse=True)
    
    logger.debug(f"Encontrados {len(backups)} backups")
    return backups


def restore_database(backup_path: str) -> None:
    """
    Restaurar base de datos desde un backup
    
    Args:
        backup_path: Ruta del archivo de backup
    
    Raises:
        FileNotFoundError: Si el backup no existe
        ValueError: Si la base de datos actual es :memory:
    
    ADVERTENCIA: Esta operación sobrescribe la base de datos actual.
    Se recomienda hacer un backup antes de restaurar.
    """
    
    backup_file = Path(backup_path)
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup no encontrado: {backup_path}")
    
    
    try:
        # Crear backup de seguridad antes de restaurar
        
        # Restaurar desde backup
        shutil.copy2(str(backup_file), str(db_path))
        
        logger.info(f"✓ Base de datos restaurada desde: {backup_path}")
    
    except Exception as e:
        logger.error(f"✗ Error restaurando backup: {str(e)}")
        raise IOError(f"Falló la restauración: {str(e)}")
