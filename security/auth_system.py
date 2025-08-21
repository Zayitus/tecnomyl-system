# security/auth_system.py - Sistema de autenticación y seguridad
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import sqlite3
import json
from functools import wraps

@dataclass
class User:
    """Representa un usuario del sistema"""
    user_id: str
    username: str
    role: str  # 'employee', 'hr', 'supervisor', 'admin'
    permissions: List[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_attempts: int = 0

@dataclass
class APIKey:
    """Representa una clave API"""
    key_id: str
    key_hash: str
    user_id: str
    name: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    usage_count: int = 0
    last_used: Optional[datetime] = None

class SecurityManager:
    """Gestor de seguridad y autenticación"""
    
    def __init__(self, database_path: str = 'test.db', 
                 jwt_secret: str = None):
        self.database_path = database_path
        self.jwt_secret = jwt_secret or self._generate_jwt_secret()
        self.session_timeout = timedelta(hours=8)
        self.max_failed_attempts = 5
        self.rate_limits = {
            'login': {'max_requests': 5, 'window': 300},  # 5 requests per 5 minutes
            'api': {'max_requests': 100, 'window': 3600}  # 100 requests per hour
        }
        self._init_security_tables()
        self._create_default_users()
    
    def _generate_jwt_secret(self) -> str:
        """Genera una clave secreta para JWT"""
        return secrets.token_urlsafe(64)
    
    def _init_security_tables(self):
        """Inicializa las tablas de seguridad"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                permissions TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME NOT NULL,
                last_login DATETIME,
                failed_attempts INTEGER DEFAULT 0
            )
        """)
        
        # Tabla de claves API
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id TEXT PRIMARY KEY,
                key_hash TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                permissions TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Tabla de sesiones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Tabla de logs de seguridad
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN NOT NULL,
                details TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        print("[SECURITY] Tablas de seguridad inicializadas")
    
    def _create_default_users(self):
        """Crea usuarios por defecto si no existen"""
        default_users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin',
                'permissions': ['all']
            },
            {
                'username': 'hr_manager',
                'password': 'hr123',
                'role': 'hr',
                'permissions': ['view_absences', 'manage_employees', 'generate_reports']
            }
        ]
        
        for user_data in default_users:
            if not self._user_exists(user_data['username']):
                self.create_user(
                    username=user_data['username'],
                    password=user_data['password'],
                    role=user_data['role'],
                    permissions=user_data['permissions']
                )
                print(f"[SECURITY] Usuario por defecto creado: {user_data['username']}")
    
    def _user_exists(self, username: str) -> bool:
        """Verifica si un usuario existe"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def _hash_password(self, password: str) -> str:
        """Hash de contraseña con salt"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
        return f"{salt}:{password_hash.hex()}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica una contraseña"""
        try:
            salt, hash_hex = password_hash.split(':')
            calculated_hash = hashlib.pbkdf2_hmac('sha256',
                                                password.encode('utf-8'),
                                                salt.encode('utf-8'),
                                                100000)
            return calculated_hash.hex() == hash_hex
        except:
            return False
    
    def create_user(self, username: str, password: str, role: str,
                   permissions: List[str]) -> str:
        """Crea un nuevo usuario"""
        user_id = secrets.token_urlsafe(16)
        password_hash = self._hash_password(password)
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (user_id, username, password_hash, role, 
                                 permissions, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, username, password_hash, role,
                json.dumps(permissions), True, datetime.now().isoformat()
            ))
            
            conn.commit()
            self._log_security_event(user_id, 'user_created', True, 
                                   f"Usuario creado: {username}, rol: {role}")
            
            return user_id
        
        except Exception as e:
            print(f"[SECURITY] Error creando usuario: {e}")
            return None
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str = None) -> Tuple[bool, Optional[User]]:
        """Autentica un usuario"""
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            # Buscar usuario
            cursor.execute("""
                SELECT user_id, username, password_hash, role, permissions, 
                       is_active, created_at, failed_attempts
                FROM users WHERE username = ?
            """, (username,))
            
            row = cursor.fetchone()
            if not row:
                self._log_security_event(None, 'login_failed', False, 
                                       f"Usuario no encontrado: {username}",
                                       ip_address)
                return False, None
            
            user_id, username, password_hash, role, permissions_json, \
            is_active, created_at, failed_attempts = row
            
            # Verificar si la cuenta está bloqueada
            if failed_attempts >= self.max_failed_attempts:
                self._log_security_event(user_id, 'login_blocked', False,
                                       f"Cuenta bloqueada por intentos fallidos",
                                       ip_address)
                return False, None
            
            # Verificar si está activo
            if not is_active:
                self._log_security_event(user_id, 'login_inactive', False,
                                       f"Cuenta inactiva", ip_address)
                return False, None
            
            # Verificar contraseña
            if not self._verify_password(password, password_hash):
                # Incrementar intentos fallidos
                cursor.execute("""
                    UPDATE users SET failed_attempts = failed_attempts + 1
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
                
                self._log_security_event(user_id, 'login_failed', False,
                                       f"Contraseña incorrecta", ip_address)
                return False, None
            
            # Login exitoso - resetear intentos fallidos y actualizar last_login
            cursor.execute("""
                UPDATE users SET failed_attempts = 0, last_login = ?
                WHERE user_id = ?
            """, (datetime.now().isoformat(), user_id))
            conn.commit()
            
            permissions = json.loads(permissions_json)
            user = User(
                user_id=user_id,
                username=username,
                role=role,
                permissions=permissions,
                is_active=is_active,
                created_at=datetime.fromisoformat(created_at),
                last_login=datetime.now()
            )
            
            self._log_security_event(user_id, 'login_success', True,
                                   f"Login exitoso", ip_address)
            
            return True, user
        
        except Exception as e:
            print(f"[SECURITY] Error en autenticación: {e}")
            return False, None
        finally:
            conn.close()
    
    def create_jwt_token(self, user: User, ip_address: str = None) -> str:
        """Crea un token JWT para el usuario"""
        payload = {
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role,
            'permissions': user.permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + self.session_timeout
        }
        
        if ip_address:
            payload['ip'] = ip_address
        
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        
        # Crear sesión en BD
        self._create_session(user.user_id, ip_address)
        
        return token
    
    def verify_jwt_token(self, token: str, ip_address: str = None) -> Tuple[bool, Optional[User]]:
        """Verifica un token JWT"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Verificar IP si está en el token
            if 'ip' in payload and ip_address and payload['ip'] != ip_address:
                self._log_security_event(payload.get('user_id'), 'token_ip_mismatch', 
                                       False, f"IP mismatch: {ip_address} vs {payload['ip']}")
                return False, None
            
            # Crear objeto User desde payload
            user = User(
                user_id=payload['user_id'],
                username=payload['username'],
                role=payload['role'],
                permissions=payload['permissions'],
                is_active=True,
                created_at=datetime.now()  # Placeholder
            )
            
            return True, user
            
        except jwt.ExpiredSignatureError:
            self._log_security_event(None, 'token_expired', False, "Token expirado")
            return False, None
        except jwt.InvalidTokenError:
            self._log_security_event(None, 'token_invalid', False, "Token inválido")
            return False, None
    
    def create_api_key(self, user_id: str, name: str, 
                      permissions: List[str], expires_in_days: int = 365) -> str:
        """Crea una nueva clave API"""
        
        key_id = secrets.token_urlsafe(16)
        api_key = f"tek_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO api_keys (key_id, key_hash, user_id, name, permissions,
                                    created_at, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key_id, key_hash, user_id, name, json.dumps(permissions),
                datetime.now().isoformat(), expires_at.isoformat(), True
            ))
            
            conn.commit()
            self._log_security_event(user_id, 'api_key_created', True,
                                   f"API key creada: {name}")
            
            return api_key
        
        except Exception as e:
            print(f"[SECURITY] Error creando API key: {e}")
            return None
        finally:
            conn.close()
    
    def verify_api_key(self, api_key: str) -> Tuple[bool, Optional[User]]:
        """Verifica una clave API"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT ak.user_id, ak.permissions, ak.expires_at, ak.is_active,
                       u.username, u.role, u.is_active as user_active
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.user_id
                WHERE ak.key_hash = ?
            """, (key_hash,))
            
            row = cursor.fetchone()
            if not row:
                self._log_security_event(None, 'api_key_invalid', False,
                                       "API key no encontrada")
                return False, None
            
            user_id, permissions_json, expires_at, is_active, \
            username, role, user_active = row
            
            # Verificar si está activa
            if not is_active or not user_active:
                self._log_security_event(user_id, 'api_key_inactive', False,
                                       "API key o usuario inactivo")
                return False, None
            
            # Verificar expiración
            if expires_at:
                expire_date = datetime.fromisoformat(expires_at)
                if datetime.now() > expire_date:
                    self._log_security_event(user_id, 'api_key_expired', False,
                                           "API key expirada")
                    return False, None
            
            # Actualizar uso
            cursor.execute("""
                UPDATE api_keys SET usage_count = usage_count + 1,
                                   last_used = ?
                WHERE key_hash = ?
            """, (datetime.now().isoformat(), key_hash))
            conn.commit()
            
            permissions = json.loads(permissions_json)
            user = User(
                user_id=user_id,
                username=username,
                role=role,
                permissions=permissions,
                is_active=True,
                created_at=datetime.now()  # Placeholder
            )
            
            return True, user
            
        except Exception as e:
            print(f"[SECURITY] Error verificando API key: {e}")
            return False, None
        finally:
            conn.close()
    
    def _create_session(self, user_id: str, ip_address: str = None):
        """Crea una nueva sesión"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + self.session_timeout
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (session_id, user_id, created_at, expires_at, 
                                is_active, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id, user_id, datetime.now().isoformat(),
            expires_at.isoformat(), True, ip_address
        ))
        
        conn.commit()
        conn.close()
    
    def _log_security_event(self, user_id: str, action: str, success: bool,
                           details: str, ip_address: str = None):
        """Registra un evento de seguridad"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO security_logs (timestamp, user_id, action, ip_address,
                                     success, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(), user_id, action, ip_address,
            success, details
        ))
        
        conn.commit()
        conn.close()
    
    def check_permission(self, user: User, required_permission: str) -> bool:
        """Verifica si un usuario tiene un permiso específico"""
        if 'all' in user.permissions:
            return True
        return required_permission in user.permissions
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de seguridad"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Contadores básicos
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM api_keys WHERE is_active = 1")
        active_api_keys = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
        active_sessions = cursor.fetchone()[0]
        
        # Eventos de seguridad recientes (última hora)
        hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute("""
            SELECT action, success, COUNT(*) 
            FROM security_logs 
            WHERE timestamp > ?
            GROUP BY action, success
        """, (hour_ago,))
        
        recent_events = {}
        for action, success, count in cursor.fetchall():
            key = f"{action}_{'success' if success else 'failed'}"
            recent_events[key] = count
        
        conn.close()
        
        return {
            'active_users': active_users,
            'active_api_keys': active_api_keys,
            'active_sessions': active_sessions,
            'recent_events': recent_events,
            'last_updated': datetime.now().isoformat()
        }

# Decoradores para autenticación
def require_auth(permission: str = None):
    """Decorador que requiere autenticación JWT"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # En una aplicación real, se obtendría del header Authorization
            # Este es un ejemplo simplificado
            token = kwargs.get('auth_token')
            if not token:
                return {'error': 'Token de autenticación requerido'}, 401
            
            security_manager = SecurityManager()
            valid, user = security_manager.verify_jwt_token(token)
            
            if not valid:
                return {'error': 'Token inválido o expirado'}, 401
            
            if permission and not security_manager.check_permission(user, permission):
                return {'error': 'Permisos insuficientes'}, 403
            
            kwargs['current_user'] = user
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_api_key(permission: str = None):
    """Decorador que requiere clave API"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            api_key = kwargs.get('api_key')
            if not api_key:
                return {'error': 'Clave API requerida'}, 401
            
            security_manager = SecurityManager()
            valid, user = security_manager.verify_api_key(api_key)
            
            if not valid:
                return {'error': 'Clave API inválida'}, 401
            
            if permission and not security_manager.check_permission(user, permission):
                return {'error': 'Permisos insuficientes'}, 403
            
            kwargs['current_user'] = user
            return func(*args, **kwargs)
        return wrapper
    return decorator

def test_security_system():
    """Función de prueba del sistema de seguridad"""
    print("[TEST] Sistema de Seguridad y Autenticación")
    print("=" * 55)
    
    security_manager = SecurityManager()
    
    # Test de autenticación de usuario por defecto
    print("\n[AUTH] Probando autenticación...")
    success, admin_user = security_manager.authenticate_user('admin', 'admin123', '127.0.0.1')
    
    if success:
        print(f"  Login exitoso: {admin_user.username} ({admin_user.role})")
        print(f"  Permisos: {admin_user.permissions}")
        
        # Crear token JWT
        token = security_manager.create_jwt_token(admin_user, '127.0.0.1')
        print(f"  Token JWT generado (longitud: {len(token)})")
        
        # Verificar token
        valid, token_user = security_manager.verify_jwt_token(token, '127.0.0.1')
        if valid:
            print(f"  Token verificado correctamente para: {token_user.username}")
        
        # Crear API key
        api_key = security_manager.create_api_key(
            admin_user.user_id, 
            "Test API Key", 
            ['view_absences', 'manage_employees']
        )
        print(f"  API Key creada: {api_key[:15]}...")
        
        # Verificar API key
        valid, api_user = security_manager.verify_api_key(api_key)
        if valid:
            print(f"  API Key verificada para: {api_user.username}")
            print(f"  Permisos API: {api_user.permissions}")
    
    # Estadísticas de seguridad
    print(f"\n[STATS] Estadísticas de seguridad:")
    stats = security_manager.get_security_stats()
    print(f"  Usuarios activos: {stats['active_users']}")
    print(f"  API Keys activas: {stats['active_api_keys']}")
    print(f"  Sesiones activas: {stats['active_sessions']}")
    print(f"  Eventos recientes: {stats['recent_events']}")
    
    # Test de permisos
    print(f"\n[PERMISSIONS] Probando sistema de permisos...")
    if success:
        has_all = security_manager.check_permission(admin_user, 'all')
        has_view = security_manager.check_permission(admin_user, 'view_absences')
        has_invalid = security_manager.check_permission(admin_user, 'invalid_permission')
        
        print(f"  Permiso 'all': {has_all}")
        print(f"  Permiso 'view_absences': {has_view}")
        print(f"  Permiso inválido: {has_invalid}")

if __name__ == "__main__":
    test_security_system()