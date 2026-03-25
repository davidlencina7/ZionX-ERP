import sys
def verify_venv():
    # Prevenir ejecución fuera de entorno virtual (.venv)
    # Compatible con Python 3.8+ y variantes
    import os
    venv = os.environ.get('VIRTUAL_ENV')
    exe = sys.executable.lower()
    cwd = os.getcwd().lower()
    # Detectar si el ejecutable de Python está dentro de la carpeta .venv
    if not venv or ".venv" not in exe and ".venv" not in cwd:
        raise RuntimeError(
            "La aplicación debe ejecutarse dentro del entorno virtual (.venv)"
        )
def verify_dependencies():
    try:
        import reportlab
        from reportlab.platypus import SimpleDocTemplate
    except ImportError as e:
        raise RuntimeError(
            "Missing required dependency: reportlab. "
            "Install with: pip install reportlab"
        ) from e
# INFRASTRUCTURE FROZEN – v1.0 STABLE
# No modificar sin justificación técnica crítica.
"""
Flask App Factory para ZionX ERP
Configuración centralizada con patrón factory + autenticación
"""
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
import sys
from pathlib import Path

# Agregar directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Instancias globales
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name: str = None) -> Flask:
    """
    Factory para crear instancia de Flask
    
    Args:
        config_name: Nombre de configuración (development, production, testing)
    
    Returns:
        Aplicación Flask configurada
    """
    # Determinar rutas absolutas para frontend
    root_dir = Path(__file__).parent.parent.parent
    templates_dir = root_dir / "frontend" / "templates"
    static_dir = root_dir / "frontend" / "assets"

    # Validar entorno virtual y dependencias críticas (fail fast)
    verify_venv()
    verify_dependencies()

    app = Flask(
        __name__,
        template_folder=str(templates_dir),
        static_folder=str(static_dir)
    )

    # Configurar según entorno
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    configure_app(app, config_name)
    configure_auth(app)
    csrf.init_app(app)  # Inicializar protección CSRF
    configure_tema_handler(app)  # Inicializar manejador de tema
    register_blueprints(app)
    register_error_handlers(app)

    return app


def configure_tema_handler(app: Flask) -> None:
    """Configurar manejador automático de tema en sesión"""
    
    @app.before_request
    def inicializar_tema():
        """Inicializar tema en sesión si no existe"""
        from flask import session, request
        
        # Solo inicializar si no está en sesión
        if 'tema' not in session:
            session['tema'] = 'light'
        def setup_bootstrap_logging():
            import os
            import logging
            log_dir = os.path.abspath("logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "piupiu.log")
            logging.basicConfig(
                level=logging.CRITICAL,
                format="%(asctime)s [%(levelname)s] %(message)s",
                handlers=[
                    logging.FileHandler(log_path),
                    logging.StreamHandler()
                ]
            )

        # Bootstrap logging mínimo para errores críticos antes de cualquier validación
        setup_bootstrap_logging()


def configure_app(app: Flask, config_name: str) -> None:
    """Configurar la aplicación Flask"""
    
    # Bloqueo real de arranque en production si falta SECRET_KEY
    import logging
    secret_key = os.environ.get('SECRET_KEY')

    if app.config.get("ENV") == "production":
        if not secret_key:
            # Logging mínimo CRITICAL para asegurar registro aunque no esté inicializado el logging avanzado
            logging.basicConfig(level=logging.CRITICAL, filename='logs/piupiu.log',
                                format='%(asctime)s %(levelname)s %(name)s %(message)s')
            logging.critical("SECRET_KEY no definida en entorno production. Abortando arranque.")
            raise RuntimeError("SECRET_KEY obligatoria en producción.")
        app.config['SECRET_KEY'] = secret_key
    else:
        # Si estamos en modo desktop, generar SECRET_KEY automática segura si no existe
        if os.environ.get('PIUPIU_DESKTOP_MODE') == '1' and not secret_key:
            import secrets
            secret_key = secrets.token_hex(32)  # 64 caracteres hexadecimales
        app.config['SECRET_KEY'] = secret_key or 'dev-secret-key-piupiu-2026-CAMBIAR-EN-PRODUCCION'
    
    # Configuraciones según entorno
    if config_name == 'development' or os.environ.get('MODE') == 'dev':
        app.config['DEBUG'] = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Desactivar CSRF en desarrollo
    elif config_name == 'production':
        app.config['DEBUG'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = False
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['REMEMBER_COOKIE_SECURE'] = True
        app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    elif config_name == 'testing':
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
    
    # CSRF Protection
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # Sin límite de tiempo
    
    # Configuración de la base de datos

    # Eliminado: configuración de DATABASE_PATH (solo PostgreSQL)

    # Si se desea iniciar el servicio de sincronización junto al backend en producción,
    # se puede importar y lanzar el hilo aquí de forma similar a dev_server.py
    # from sync_service import main as start_sync_service
    # threading.Thread(target=start_sync_service, daemon=True).start()


def configure_auth(app: Flask) -> None:
    """Configurar Flask-Login"""
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Redirigir directamente al login
    login_manager.login_message = 'Por favor inicia sesión para acceder'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from backend.services.auth_service import AuthService
        auth_service = AuthService()
        return auth_service.obtener_usuario_por_id(int(user_id))
    
    # Context processor para hacer session disponible en templates
    @app.context_processor
    def inject_session():
        from flask import session
        from flask_wtf.csrf import generate_csrf
        return {
            'session': session,
            'app_config': app.config,
            'csrf_token': generate_csrf
        }


def register_blueprints(app: Flask) -> None:
    """Registrar todos los blueprints"""
    
    # Blueprints existentes
    from backend.controllers.dashboard import dashboard_bp
    from backend.controllers.compras import compras_bp
    from backend.controllers.ventas import ventas_bp
    from backend.controllers.inventario import inventario_bp
    from backend.controllers.reportes import reportes_bp
    
    # Blueprints nuevos
    from backend.controllers.auth import auth_bp
    from backend.controllers.gastos import gastos_bp
    from backend.controllers.activos import activos_bp
    from backend.controllers.contabilidad import contabilidad_bp
    from backend.controllers.sistema import sistema_bp
    from backend.controllers.operativo import operativo_bp
    from backend.controllers.gerencial import gerencial_bp
    
    # Blueprints operativo y gerencial (simplificados)
    from backend.controllers.operativo import operativo_bp
    from backend.controllers.gerencial import gerencial_bp
    
    # Blueprint de operaciones (modo operativo inmediato)

    from backend.controllers.operaciones import operaciones_bp
    from backend.controllers.configuracion import configuracion_bp
    from backend.controllers.config_api import config_api_bp
    from backend.controllers.diagnostico_history import diagnostico_history_bp
    from backend.controllers.diagnostico_scheduler import scheduler_bp
    from backend.controllers.diagnostico_plugins import diagnostico_plugins_bp


    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(compras_bp, url_prefix='/compras')
    app.register_blueprint(ventas_bp, url_prefix='/ventas')
    app.register_blueprint(inventario_bp, url_prefix='/inventario')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(gastos_bp, url_prefix='/gastos')
    app.register_blueprint(activos_bp, url_prefix='/activos')
    app.register_blueprint(contabilidad_bp, url_prefix='/contabilidad')
    app.register_blueprint(operativo_bp, url_prefix='/operativo')
    app.register_blueprint(gerencial_bp, url_prefix='/gerencial')
    app.register_blueprint(sistema_bp, url_prefix='/sistema')
    app.register_blueprint(operaciones_bp, url_prefix='/operaciones')
    app.register_blueprint(configuracion_bp, url_prefix='')
    app.register_blueprint(config_api_bp, url_prefix='')
    app.register_blueprint(diagnostico_history_bp, url_prefix='')
    app.register_blueprint(diagnostico_plugins_bp, url_prefix='')
    app.register_blueprint(scheduler_bp, url_prefix='')


def register_error_handlers(app: Flask) -> None:
    """Registrar manejadores de errores"""
    
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('error.html', error_code=404, error_message='Página no encontrada'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        from flask import render_template
        return render_template('error.html', error_code=500, error_message='Error interno del servidor'), 500

    # Manejador global para devolver errores como JSON en modo API
    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        from flask import jsonify, request
        # Si es petición API, devolver JSON
        if request.path.startswith('/api/'):
            return jsonify({
                'error': str(e),
                'type': type(e).__name__,
                'trace': traceback.format_exc().splitlines()[-2:]
            }), 500
        # Si no, usar el manejador por defecto
        raise e

