"""
PIU PIU - Sistema de Gestión de Negocio
Versión 3.0.0 - Arquitectura escalable
"""
from backend.database.connection import DatabaseConnection
from backend.services import (
    ProductosService,
    ComprasService,
    VentasService,
    ReportesService
)
from backend.core.app_factory import create_app

__all__ = [
    'DatabaseConnection',
    'ProductosService',
    'ComprasService',
    'VentasService',
    'ReportesService',
    'create_app'
]
