# INFRASTRUCTURE FROZEN – v1.0 STABLE
# No modificar sin justificación técnica crítica.
"""
Configuración centralizada de la aplicación ZionX
Carga variables de entorno desde .env y configura logging
"""
import os
from dotenv import load_dotenv
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Union

load_dotenv('.env.production')
# Importar sistema de versionado centralizado
from backend.core.version import (
    __version__,
    VERSION,
    APP_NAME,
    APP_NAME_FULL,
    get_version,
    get_version_string,
    get_environment
)

# ==================== RUTAS ====================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = BASE_DIR / 'app'
DATA_DIR = BASE_DIR / 'data'

# Carpeta de logs accesible para el usuario (evita errores de permisos en instalaciones)
try:
    appdata = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
    if appdata:
        LOGS_DIR = Path(appdata) / 'PIUPIU_ERP_logs'
    else:
        LOGS_DIR = Path.home() / 'PIUPIU_ERP_logs'
except Exception:
    # Fallback: usar carpeta local
    LOGS_DIR = BASE_DIR / 'logs'

TESTS_DIR = BASE_DIR / 'tests'

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ==================== CONFIGURACIÓN DESDE .env ====================
def cargar_env() -> None:
    """Cargar variables de entorno desde .env"""
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith('#') and '=' in linea:
                    clave, valor = linea.split('=', 1)
                    os.environ.setdefault(clave.strip(), valor.strip())

cargar_env()

# ==================== APLICACIÓN ====================
# VERSIÓN Y NOMBRE: Importados de backend.core.version (arriba)
# APP_NAME, VERSION ya están disponibles globalmente desde el import
MODE = os.getenv('MODE', 'cli').lower()
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'


# ==================== BASE DE DATOS ====================


# Usar solo DATABASE_URL del entorno (PostgreSQL). Si no está definida, lanzar error.
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL no está definida. Configura tu .env.production correctamente.')

# ==================== LOGGING ====================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE = LOGS_DIR / os.getenv('LOG_FILE', 'piupiu.log').replace('logs/', '')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'standard')  # 'standard' o 'json'

# Mapeo de niveles de log
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

def configurar_logger(
    nombre: str = 'piupiu',
    nivel: Optional[int] = None,
    archivo: Optional[Path] = None
) -> logging.Logger:
    """
    Configurar un logger centralizado
    
    Args:
        nombre: Nombre del logger
        nivel: Nivel de log (DEBUG, INFO, etc)
        archivo: Ruta del archivo de log
    
    Returns:
        Logger configurado
    """
    if nivel is None:
        nivel = LOG_LEVEL_MAP.get(LOG_LEVEL, logging.INFO)
    
    if archivo is None:
        archivo = LOG_FILE
    
    logger = logging.getLogger(nombre)
    logger.setLevel(nivel)
    
    # Evitar handlers duplicados
    if not logger.handlers:
        # Formato
        formatter: logging.Formatter
        if LOG_FORMAT == 'json':
            try:
                from pythonjsonlogger import jsonlogger  # type: ignore
                formatter = jsonlogger.JsonFormatter(
                    '%(asctime)s %(levelname)s %(name)s %(message)s'
                )
            except Exception:
                formatter = logging.Formatter(
                    '[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
        else:
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Handler de archivo (rotativo 10MB, 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            str(archivo),
            maxBytes=10485760,
            backupCount=5
        )
        file_handler.setLevel(nivel)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler de consola (solo en DEBUG/DEV)
        if DEBUG or MODE == 'dev':
            console_handler = logging.StreamHandler()
            console_handler.setLevel(nivel)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    return logger

# Logger global
logger = configurar_logger()

# ==================== PRODUCTOS POR DEFECTO ====================
PRODUCTOS_INICIALES = [
    'pollo entero',
    'pata muslo',
    'maple de huevos'
]

# ==================== CONFIGURACIÓN DE DESARROLLO ====================
DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'False').lower() == 'true'
SHOW_TRACEBACK = os.getenv('SHOW_TRACEBACK', 'False').lower() == 'true'

# Si estamos en modo dev, activar debug y traceback
if MODE == 'dev':
    DEBUG = True
    SHOW_TRACEBACK = True
    logger.setLevel(logging.DEBUG)
    LOG_LEVEL = 'DEBUG'

# ==================== INFORMACIÓN DE CONFIGURACIÓN ====================
if __name__ == '__main__':
    print(f"""
    ===== CONFIGURACIÓN ZionX =====
    
    Aplicación: {APP_NAME}
    Versión: {VERSION}
    Modo: {MODE}
    Debug: {DEBUG}
    
    Rutas:
    - Base: {BASE_DIR}
    - Datos: {DATA_DIR}
    - Logs: {LOGS_DIR}
    - BD: PostgreSQL
    
    Logging:
    - Nivel: {LOG_LEVEL}
    - Archivo: {LOG_FILE}
    - Formato: {LOG_FORMAT}
    
    ==================================
    """)

