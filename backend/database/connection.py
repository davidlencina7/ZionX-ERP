"""
Gestión centralizada de conexiones a base de datos (solo PostgreSQL) con logging y type hints
"""


import logging
from typing import Optional, Union
import os
import psycopg2
from dotenv import load_dotenv
from backend.config.settings import logger

class DatabaseConnection:
    """Gestor de conexiones a la base de datos PostgreSQL (patrón Singleton)"""

    _instance = None

    def __init__(self):
        logger.debug("DatabaseConnection inicializado (solo PostgreSQL)")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_connection(self):
        """Obtener una nueva conexión a la base de datos PostgreSQL"""
        # Cargar variables de entorno desde .env.production si no están cargadas
        if not os.environ.get('DATABASE_URL'):
            load_dotenv('.env.production')

        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL no está definida. Configura tu .env.production correctamente.")
            raise RuntimeError("DATABASE_URL no está definida. Configura tu .env.production correctamente.")

        try:
            conn = psycopg2.connect(database_url)
            logger.debug("Conexión a PostgreSQL establecida correctamente")
            return conn
        except Exception as e:
            logger.error(f"Error al conectar a PostgreSQL: {e}")
            raise

    def init_db(self):
        """Inicializar la base de datos PostgreSQL (no implementado aquí)"""
        raise NotImplementedError("Inicialización solo para PostgreSQL")
