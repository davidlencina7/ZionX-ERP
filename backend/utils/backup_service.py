import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
import sqlite3



BACKUP_DIR = Path(__file__).parent.parent.parent / 'backups'
LOGS_DIR = Path(__file__).parent.parent.parent / 'logs'
BACKUP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / 'app.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=1_048_576,  # 1MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

def get_db_path():
    # Aquí se debe ajustar para usar la configuración de PostgreSQL si aplica
    raise NotImplementedError("Función de backup no implementada para PostgreSQL.")

def backup_database():
    db_path = get_db_path()
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return None
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    backup_path = BACKUP_DIR / backup_name
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Backup creado: {backup_path}")
        rotate_backups()
        return backup_path
    except Exception as e:
        logger.error(f"Error creando backup: {e}")
        return None

def rotate_backups():
    backups = sorted(BACKUP_DIR.glob('piupiu_*.db'), key=lambda f: f.stat().st_mtime, reverse=True)
    for old_backup in backups[7:]:
        try:
            old_backup.unlink()
            logger.info(f"Backup antiguo eliminado: {old_backup}")
        except Exception as e:
            logger.error(f"Error eliminando backup: {old_backup} - {e}")

def check_integrity():
    db_path = get_db_path()
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return 'error'
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        result = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
        conn.close()
        if result == 'ok':
            logger.info(f"Integridad OK para {db_path}")
        else:

            logger.error(f"Integridad fallida para {db_path}: {result}")
