"""
Servicio de autenticación de usuarios
"""
import logging
import bcrypt
import re
from typing import Optional
from datetime import datetime, timedelta

from backend.database.connection import DatabaseConnection
from backend.models.usuario import Usuario

logger = logging.getLogger(__name__)

# Límites de seguridad
MAX_INTENTOS_LOGIN = 99
TIEMPO_BLOQUEO_MINUTOS = 0.1


class AuthService:
    """Servicio para gestionar autenticación de usuarios"""
    
    def __init__(self) -> None:
        self.db = DatabaseConnection.get_instance()
        self.intentos_fallidos = {}  # username -> (contador, timestamp_bloqueo)
        logger.debug("AuthService inicializado")
    
    def crear_usuario(
        self,
        username: str,
        password: str,
        nombre_completo: str,
        email: Optional[str] = None,
        rol: str = 'usuario'
    ) -> Usuario:
        """
        Crear un nuevo usuario
        
        Args:
            username: Nombre de usuario único
            password: Contraseña en texto plano
            nombre_completo: Nombre completo del usuario
            email: Email opcional
            rol: 'admin' o 'usuario'
        
        Returns:
            Usuario creado
        
        Raises:
            ValueError: Si el usuario ya existe o datos inválidos
        """
        if not username or len(username) < 3:
            raise ValueError("El username debe tener al menos 3 caracteres")
        
        # Validación fuerte de contraseña
        if not self._validar_password_fuerte(password):
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres, "
                "incluyendo al menos 1 número y 1 letra"
            )
        
        # Hash de la contraseña
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, nombre_completo, email, rol))
            
            conn.commit()
            usuario_id = cursor.lastrowid
            
            logger.info(f"Usuario creado: {username} (ID: {usuario_id})")
            
            return Usuario(
                id=usuario_id,
                username=username,
                nombre_completo=nombre_completo,
                email=email,
                rol=rol
            )
        
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear usuario {username}: {str(e)}")
            raise ValueError(f"No se pudo crear el usuario: {str(e)}")
        
        finally:
            conn.close()
    
    def autenticar_usuario(self, username: str, password: str) -> Optional[Usuario]:
        """
        Autenticar usuario por username y password con límite de intentos
        
        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano
        
        Returns:
            Usuario si las credenciales son correctas, None si no
        
        Raises:
            ValueError: Si la cuenta está temporalmente bloqueada
        """
        # Verificar si está bloqueado
        if self._esta_bloqueado(username):
            raise ValueError(f"Cuenta temporalmente bloqueada. Intenta en {TIEMPO_BLOQUEO_MINUTOS} minutos.")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, password_hash, nombre_completo, email, rol, 
                       activo, tema_preferido, fecha_creacion, ultimo_acceso
                FROM usuarios
                WHERE username = %s AND activo = TRUE
            ''', (username,))

            row = cursor.fetchone()

            if not row:
                logger.warning(f"Intento de login fallido: usuario '{username}' no encontrado")
                self._registrar_intento_fallido(username)
                return None

            # Verificar password
            password_hash = row[2]
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                logger.warning(f"Intento de login fallido: contraseña incorrecta para '{username}'")
                self._registrar_intento_fallido(username)
                return None

            # Login exitoso - resetear intentos fallidos
            self._resetear_intentos(username)

            # Actualizar último acceso
            cursor.execute('''
                UPDATE usuarios SET ultimo_acceso = %s WHERE id = %s
            ''', (datetime.now(), row[0]))
            conn.commit()

            logger.info(f"Login exitoso: {username}")

            return Usuario(
                id=row[0],
                username=row[1],
                nombre_completo=row[3],
                email=row[4],
                rol=row[5],
                activo=bool(row[6]),
                tema_preferido=row[7],
                fecha_creacion=row[8],
                ultimo_acceso=row[9]
            )
        except Exception as e:
            print(f"[ERROR AUTENTICACIÓN] {e}")
            logger.error(f"[ERROR AUTENTICACIÓN] {e}")
            raise
        finally:
            conn.close()
    
    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """
        Obtener usuario por ID
        
        Args:
            usuario_id: ID del usuario
        
        Returns:
            Usuario si existe, None si no
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, nombre_completo, email, rol, activo, 
                       tema_preferido, fecha_creacion, ultimo_acceso
                FROM usuarios
                WHERE id = %s
            ''', (usuario_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return Usuario(
                id=row[0],
                username=row[1],
                nombre_completo=row[2],
                email=row[3],
                rol=row[4],
                activo=bool(row[5]),
                tema_preferido=row[6],
                fecha_creacion=row[7],
                ultimo_acceso=row[8]
            )
        
        finally:
            conn.close()
    
    def cambiar_password(self, usuario_id: int, password_actual: str, password_nuevo: str) -> bool:
        """
        Cambiar contraseña de usuario
        
        Args:
            usuario_id: ID del usuario
            password_actual: Contraseña actual
            password_nuevo: Nueva contraseña
        
        Returns:
            True si se cambió, False si no
        """
        if len(password_nuevo) < 6:
            raise ValueError("La nueva contraseña debe tener al menos 6 caracteres")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar password actual
            cursor.execute('SELECT password_hash FROM usuarios WHERE id = %s', (usuario_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            if not bcrypt.checkpw(password_actual.encode('utf-8'), row[0].encode('utf-8')):
                logger.warning(f"Intento de cambio de contraseña fallido: contraseña actual incorrecta")
                return False
            
            # Actualizar password
            nuevo_hash = bcrypt.hashpw(password_nuevo.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('UPDATE usuarios SET password_hash = %s WHERE id = %s', (nuevo_hash, usuario_id))
            conn.commit()
            
            logger.info(f"Contraseña cambiada exitosamente para usuario ID: {usuario_id}")
            return True
        
        finally:
            conn.close()
    
    def actualizar_tema(self, usuario_id: int, tema: str) -> bool:
        """
        Actualizar tema preferido del usuario
        
        Args:
            usuario_id: ID del usuario
            tema: 'light' o 'dark'
        
        Returns:
            True si se actualizó, False si no
        """
        if tema not in ('light', 'dark'):
            raise ValueError("Tema debe ser 'light' o 'dark'")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE usuarios SET tema_preferido = ? WHERE id = ?
            ''', (tema, usuario_id))
            conn.commit()
            
            logger.info(f"Tema actualizado a '{tema}' para usuario ID: {usuario_id}")
            return cursor.rowcount > 0
        
        finally:
            conn.close()
    
    # Métodos privados de seguridad
    
    def _validar_password_fuerte(self, password: str) -> bool:
        """
        Validar que la contraseña cumple requisitos de seguridad
        
        Requisitos:
        - Mínimo 8 caracteres
        - Al menos 1 número
        - Al menos 1 letra
        
        Args:
            password: Contraseña a validar
        
        Returns:
            True si es válida, False si no
        """
        if not password or len(password) < 8:
            return False
        
        tiene_numero = re.search(r'\d', password) is not None
        tiene_letra = re.search(r'[a-zA-Z]', password) is not None
        
        return tiene_numero and tiene_letra
    
    def _esta_bloqueado(self, username: str) -> bool:
        """Verificar si la cuenta está temporalmente bloqueada"""
        
        if username not in self.intentos_fallidos:
            return False
        
        intentos, timestamp_bloqueo = self.intentos_fallidos[username]
        
        # Si no está bloqueado aún
        if intentos < MAX_INTENTOS_LOGIN:
            return False
        
        # Verificar si ya pasó el tiempo de bloqueo
        tiempo_transcurrido = datetime.now() - timestamp_bloqueo
        if tiempo_transcurrido.total_seconds() / 60 >= TIEMPO_BLOQUEO_MINUTOS:
            # Resetear intentos después del bloqueo
            self._resetear_intentos(username)
            return False
        
        return True
    
    def _registrar_intento_fallido(self, username: str) -> None:
        """Registrar un intento fallido de login"""
        
        if username not in self.intentos_fallidos:
            self.intentos_fallidos[username] = [1, datetime.now()]
        else:
            intentos, _ = self.intentos_fallidos[username]
            intentos += 1
            
            if intentos >= MAX_INTENTOS_LOGIN:
                # Bloquear cuenta
                self.intentos_fallidos[username] = [intentos, datetime.now()]
                logger.warning(f"Cuenta '{username}' bloqueada temporalmente por {TIEMPO_BLOQUEO_MINUTOS} minutos")
            else:
                self.intentos_fallidos[username] = [intentos, datetime.now()]
                logger.info(f"Intento fallido {intentos}/{MAX_INTENTOS_LOGIN} para '{username}'")
    
    def _resetear_intentos(self, username: str) -> None:
        """Resetear intentos fallidos después de login exitoso"""
        
        if username in self.intentos_fallidos:
            del self.intentos_fallidos[username]
