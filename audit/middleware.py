"""
Middleware personalizado para auditoría avanzada
Captura información adicional como IP, User-Agent, y contexto de requests
"""

import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from ipware import get_client_ip
from auditlog.context import set_actor
from auditlog.models import LogEntry

logger = logging.getLogger('auditlog')


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para capturar información detallada de auditoría en cada request
    """
    
    def process_request(self, request):
        """
        Procesa cada request para capturar información de auditoría
        """
        # Capturar IP del cliente
        client_ip, is_routable = get_client_ip(request)
        
        # Capturar User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Capturar método HTTP y path
        http_method = request.method
        request_path = request.path
        
        # Información del usuario
        user = getattr(request, 'user', AnonymousUser())
        
        # Establecer actor para auditlog
        if user and not isinstance(user, AnonymousUser):
            set_actor(user)
        
        # Guardar información adicional en el request para uso posterior
        request.audit_info = {
            'client_ip': client_ip,
            'is_routable_ip': is_routable,
            'user_agent': user_agent,
            'http_method': http_method,
            'request_path': request_path,
            'timestamp': None,  # Se establecerá en process_response
        }
        
        # Log de requests en endpoints sensibles
        sensitive_paths = [
            '/api/auth/', '/api/users/', '/api/notes/',
            '/admin/', '/api/password-reset/'
        ]
        
        if any(path in request_path for path in sensitive_paths):
            logger.info(
                f"Sensitive endpoint access: {http_method} {request_path} "
                f"by {user} from {client_ip} ({user_agent[:100]})"
            )
    
    def process_response(self, request, response):
        """
        Procesa la respuesta para completar la auditoría
        """
        if hasattr(request, 'audit_info'):
            # Registrar respuesta para endpoints sensibles
            status_code = response.status_code
            
            # Solo registrar respuestas de error o acciones importantes
            if status_code >= 400 or request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                user = getattr(request, 'user', AnonymousUser())
                
                audit_data = {
                    'action': f"{request.method} {request.path}",
                    'user': str(user) if user and not isinstance(user, AnonymousUser) else 'Anonymous',
                    'ip': request.audit_info.get('client_ip'),
                    'user_agent': request.audit_info.get('user_agent', '')[:200],
                    'status_code': status_code,
                    'is_error': status_code >= 400,
                }
                
                log_level = logging.WARNING if status_code >= 400 else logging.INFO
                logger.log(
                    log_level,
                    f"API Response: {request.method} {request.path} "
                    f"-> {status_code} by {audit_data['user']} from {audit_data['ip']}"
                )
        
        return response
    
    def process_exception(self, request, exception):
        """
        Registra excepciones para auditoría
        """
        user = getattr(request, 'user', AnonymousUser())
        client_ip = getattr(request, 'audit_info', {}).get('client_ip', 'Unknown')
        
        logger.error(
            f"Exception in {request.method} {request.path}: {str(exception)} "
            f"by {user} from {client_ip}",
            exc_info=True
        )


class AuthenticationAuditMiddleware(MiddlewareMixin):
    """
    Middleware específico para auditar eventos de autenticación
    """
    
    def process_request(self, request):
        """
        Audita intentos de login y acciones de autenticación
        """
        # Detectar intentos de login
        if request.path in ['/api/auth/login/', '/admin/login/']:
            if request.method == 'POST':
                # Capturar información del intento de login
                client_ip, _ = get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
                
                logger.info(
                    f"Login attempt from {client_ip} "
                    f"({user_agent[:100]}) to {request.path}"
                )
        
        # Detectar logout
        elif request.path in ['/api/auth/logout/', '/admin/logout/']:
            user = getattr(request, 'user', AnonymousUser())
            client_ip, _ = get_client_ip(request)
            
            if user and not isinstance(user, AnonymousUser):
                logger.info(
                    f"Logout: {user} from {client_ip}"
                )


class DataAccessAuditMiddleware(MiddlewareMixin):
    """
    Middleware para auditar acceso a datos sensibles
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Audita acceso a vistas que manejan datos sensibles
        """
        # Rutas que manejan datos sensibles
        sensitive_views = [
            'notes.views', 'users.views'
        ]
        
        view_module = getattr(view_func, '__module__', '')
        
        if any(module in view_module for module in sensitive_views):
            user = getattr(request, 'user', AnonymousUser())
            client_ip, _ = get_client_ip(request)
            
            # Registrar acceso a datos sensibles
            logger.info(
                f"Sensitive data access: {view_func.__name__} "
                f"by {user} from {client_ip} "
                f"args={view_args} kwargs={view_kwargs}"
            )


def log_successful_login(sender, user, request, **kwargs):
    """
    Signal handler para loguear logins exitosos
    """
    client_ip = 'Unknown'
    user_agent = 'Unknown'
    try:
        if request is not None:
            ip, _ = get_client_ip(request)
            client_ip = ip or 'Unknown'
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    except Exception:
        # No romper flujo si no hay request o falla ipware
        pass
    
    logger.info(
        f"Successful login: {user.username} from {client_ip} "
        f"({user_agent[:100]})"
    )


def log_failed_login(sender, credentials, request, **kwargs):
    """
    Signal handler para loguear intentos de login fallidos
    """
    client_ip = 'Unknown'
    user_agent = 'Unknown'
    try:
        if request is not None:
            ip, _ = get_client_ip(request)
            client_ip = ip or 'Unknown'
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    except Exception:
        pass
    username = credentials.get('username', 'Unknown')
    
    logger.warning(
        f"Failed login attempt: username='{username}' from {client_ip} "
        f"({user_agent[:100]})"
    )


def log_password_change(sender, user, **kwargs):
    """
    Signal handler para loguear cambios de contraseña
    """
    logger.info(f"Password changed for user: {user.username}")


def log_user_logout(sender, user, request, **kwargs):
    """
    Signal handler para loguear logout de usuarios
    """
    if user:
        client_ip = 'Unknown'
        try:
            if request is not None:
                ip, _ = get_client_ip(request)
                client_ip = ip or 'Unknown'
        except Exception:
            pass
        logger.info(f"User logout: {user.username} from {client_ip}")


# Conectar signals de Django auth para auditoría automática
try:
    from django.contrib.auth.signals import (
        user_logged_in, user_logged_out, user_login_failed
    )
    from django.contrib.auth import user_logged_in as auth_logged_in
    
    user_logged_in.connect(log_successful_login)
    user_logged_out.connect(log_user_logout)
    user_login_failed.connect(log_failed_login)
    
except ImportError:
    logger.warning("Could not import Django auth signals for audit logging")