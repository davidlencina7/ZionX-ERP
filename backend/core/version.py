
"""
PIU PIU ERP - Sistema de Versionado Centralizado
=================================================
Control de versiones semántico (SemVer) para toda la aplicación.
Formato: MAJOR.MINOR.PATCH
- MAJOR: Cambios incompatibles en API/estructura
- MINOR: Nueva funcionalidad compatible hacia atrás
- PATCH: Correcciones de bugs compatibles
Fecha de implementación: 13 de febrero de 2026
Fase 2: VERSIONADO SEMÁNTICO CENTRALIZADO
"""

import os
from datetime import datetime
from typing import Tuple


# ==================== VERSIÓN ACTUAL ====================
__version__ = "3.0.0"
__version_info__: Tuple[int, int, int] = (3, 0, 0)
VERSION = __version__

# ==================== INFORMACIÓN DE LA APLICACIÓN ====================
APP_NAME = "ZionX ERP"
APP_NAME_FULL = "ZionX - Gestión de Negocio"
APP_NAME_DESKTOP = "ZionX ERP Desktop"
APP_PUBLISHER = "ZionX"
APP_URL = "https://piupiu.com"

# ==================== METADATOS DE BUILD ====================
BUILD_DATE = "2026-02-13"
BUILD_TIMESTAMP = datetime.now().isoformat()

# Detectar entorno de ejecución
ENVIRONMENT = os.getenv('MODE', 'development').lower()
IS_PRODUCTION = ENVIRONMENT in ('prod', 'production')
IS_DEVELOPMENT = ENVIRONMENT in ('dev', 'development')
IS_DESKTOP = os.getenv('PIUPIU_DESKTOP_MODE') == '1'

# ==================== FUNCIONES PÚBLICAS ====================

def get_version() -> str:
    """
    Retorna la versión en formato string.
    
    Returns:
        str: Versión en formato "MAJOR.MINOR.PATCH"
        
    Example:
        >>> get_version()
        '3.0.0'
    """
    return __version__


def get_version_info() -> Tuple[int, int, int]:
    """
    Retorna la versión como tupla de enteros.
    """
    return __version_info__


def get_version_string() -> str:
    """
    Retorna la versión formateada con el nombre de la aplicación.
    
    Returns:
        str: Nombre y versión formateados
    
    Example:
        >>> get_version_string()
        'ZionX ERP v3.0.0'
    
    Example:
        >>> get_full_version_string()
        'ZionX - Gestión de Negocio v3.0.0'
    """
    return f"{APP_NAME_FULL} v{__version__}"


def get_desktop_version_string() -> str:
    """
    Retorna la versión formateada para aplicación desktop.
    
    Returns:
        str: Nombre desktop y versión
        
    Example:
        >>> get_desktop_version_string()
        'ZionX ERP Desktop v3.0.0'
    """
    return f"{APP_NAME_DESKTOP} v{__version__}"


def get_environment() -> str:
    """
    Retorna el entorno de ejecución actual.
    
    Returns:
        str: 'production', 'development', etc.
        
    Example:
        >>> get_environment()
        'development'
    """
    return ENVIRONMENT


def get_build_info() -> dict:
    """
    Retorna información completa del build.
    
    Returns:
        dict: Información detallada del build
        
    Example:
        >>> info = get_build_info()
        >>> print(info['version'])
        '3.0.0'
    """
    return {
        'version': __version__,
        'version_info': __version_info__,
        'version_string': get_version_string(),
        'app_name': APP_NAME,
        'app_name_full': APP_NAME_FULL,
        'build_date': BUILD_DATE,
        'build_timestamp': BUILD_TIMESTAMP,
        'environment': ENVIRONMENT,
        'is_production': IS_PRODUCTION,
        'is_development': IS_DEVELOPMENT,
        'is_desktop': IS_DESKTOP,
    }


def print_version_info():
    """
    Imprime información de versión en consola de forma legible.
    
v2.0.0 (2026-1-XX)

    Example:
        >>> print_version_info()
        ZionX ERP v3.0.0
        Build: 2026-02-13
        Environment: development
    """
    print(f"{get_version_string()}")
    print(f"Build: {BUILD_DATE}")
    print(f"Environment: {ENVIRONMENT}")
    if IS_DESKTOP:
        print("Mode: Desktop")


# ==================== CHANGELOG ====================
CHANGELOG = """
v3.0.0 (2026-02-13)
    - Versión mayor: migración a arquitectura modular.
    - Mejoras de seguridad y rendimiento.
    - Refactorización de módulos principales.

v2.0.0 (2026-01-XX)
    - Nueva interfaz de usuario.
    - Integración con sistema de reportes.
    - Corrección de errores críticos.
"""
