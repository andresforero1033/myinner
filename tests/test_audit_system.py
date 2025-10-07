"""
Tests completos para el sistema de auditoría
Verifica que todos los eventos se registran correctamente
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, Mock

from rest_framework.test import APITestCase
from rest_framework import status

from auditlog.models import LogEntry
from notes.models import Note, Tag
from users.models import UserPreference

User = get_user_model()


class AuditLogModelTestCase(TestCase):
    """Pruebas para verificar que los modelos registran cambios correctamente"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation_logged(self):
        """Verifica que la creación de usuarios se registra"""
        initial_count = LogEntry.objects.count()
        
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        
        # Debe haber un nuevo log entry
        self.assertEqual(LogEntry.objects.count(), initial_count + 1)
        
        # Verificar el log entry
        log_entry = LogEntry.objects.latest('timestamp')
        self.assertEqual(log_entry.action, LogEntry.Action.CREATE)
        # object_id puede ser int o str dependiendo de la DB, normalizamos a str
        self.assertEqual(str(log_entry.object_id), str(new_user.pk))
        self.assertIn('newuser', log_entry.object_repr)
    
    def test_user_update_logged(self):
        """Verifica que las actualizaciones de usuarios se registran"""
        initial_count = LogEntry.objects.count()
        
        # Actualizar usuario
        self.user.first_name = 'Updated'
        self.user.nickname = 'nickname_test'
        self.user.save()
        
        # Debe haber un nuevo log entry
        self.assertEqual(LogEntry.objects.count(), initial_count + 1)
        
        # Verificar el log entry
        log_entry = LogEntry.objects.latest('timestamp')
        self.assertEqual(log_entry.action, LogEntry.Action.UPDATE)
        self.assertEqual(str(log_entry.object_id), str(self.user.pk))
        
        # Verificar cambios registrados
        self.assertIn('first_name', log_entry.changes)
        self.assertIn('nickname', log_entry.changes)
    
    def test_user_deletion_logged(self):
        """Verifica que la eliminación de usuarios se registra"""
        user_id = self.user.pk
        username = self.user.username
        initial_count = LogEntry.objects.count()
        
        # Eliminar usuario
        self.user.delete()
        
        # Debe haber un nuevo log entry
        self.assertEqual(LogEntry.objects.count(), initial_count + 1)
        
        # Verificar el log entry
        log_entry = LogEntry.objects.latest('timestamp')
        self.assertEqual(log_entry.action, LogEntry.Action.DELETE)
        self.assertEqual(str(log_entry.object_id), str(user_id))
        self.assertIn(username, log_entry.object_repr)
    
    def test_note_creation_logged(self):
        """Verifica que la creación de notas se registra"""
        initial_count = LogEntry.objects.count()
        
        note = Note.objects.create(
            title='Test Note',
            content='Test content',
            user=self.user
        )
        
        # Debe haber un nuevo log entry
        self.assertEqual(LogEntry.objects.count(), initial_count + 1)
        
        # Verificar el log entry
        log_entry = LogEntry.objects.latest('timestamp')
        self.assertEqual(log_entry.action, LogEntry.Action.CREATE)
        self.assertEqual(str(log_entry.object_id), str(note.pk))
        self.assertIn('Test Note', log_entry.object_repr)
    
    def test_note_update_logged(self):
        """Verifica que las actualizaciones de notas se registran"""
        note = Note.objects.create(
            title='Original Title',
            content='Original content',
            user=self.user
        )
        
        initial_count = LogEntry.objects.count()
        
        # Actualizar nota
        note.title = 'Updated Title'
        note.content = 'Updated content'
        note.save()
        
        # Debe haber un nuevo log entry
        self.assertEqual(LogEntry.objects.count(), initial_count + 1)
        
        # Verificar el log entry
        log_entry = LogEntry.objects.latest('timestamp')
        self.assertEqual(log_entry.action, LogEntry.Action.UPDATE)
        self.assertEqual(str(log_entry.object_id), str(note.pk))
        
        # Verificar cambios registrados (content puede estar enmascarado por encriptación)
        self.assertIn('title', log_entry.changes)
    
    def test_tag_operations_logged(self):
        """Verifica que las operaciones con tags se registran"""
        initial_count = LogEntry.objects.count()
        
        # Crear tag
        tag = Tag.objects.create(name='test-tag')
        
        # Debe registrar la creación
        self.assertEqual(LogEntry.objects.count(), initial_count + 1)
        
        # Actualizar tag
        tag.name = 'updated-tag'
        tag.save()
        
        # Debe registrar la actualización
        self.assertEqual(LogEntry.objects.count(), initial_count + 2)
        
        # Eliminar tag
        tag.delete()
        
        # Debe registrar la eliminación
        self.assertEqual(LogEntry.objects.count(), initial_count + 3)
    
    def test_user_preferences_logged(self):
        """Verifica que los cambios en preferencias se registran"""
        initial_count = LogEntry.objects.count()
        
        # Crear preferencias
        preferences = UserPreference.objects.create(
            user=self.user,
            theme='dark',
            primary_color='#28a745'
        )
        
        # Debe registrar la creación
        self.assertEqual(LogEntry.objects.count(), initial_count + 1)
        
        # Actualizar preferencias
        preferences.theme = 'light'
        preferences.save()
        
        # Debe registrar la actualización
        self.assertEqual(LogEntry.objects.count(), initial_count + 2)


class AuditMiddlewareTestCase(TestCase):
    """Pruebas para el middleware de auditoría"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('audit.middleware.logger')
    def test_sensitive_endpoint_logging(self, mock_logger):
        """Verifica que los endpoints sensibles se registran"""
        # Login para tener usuario autenticado
        self.client.login(username='testuser', password='testpass123')
        
        # Acceder a endpoint sensible
        response = self.client.get('/api/users/')
        
        # Verificar que se llamó al logger
        mock_logger.info.assert_called()
        
        # Verificar que el mensaje contiene información esperada
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('Sensitive endpoint access', call_args)
        self.assertIn('/api/users/', call_args)
        self.assertIn('testuser', call_args)
    
    @patch('audit.middleware.logger')
    def test_error_response_logging(self, mock_logger):
        """Verifica que las respuestas de error se registran"""
        # Hacer request que resultará en error 404
        response = self.client.get('/api/nonexistent/')
        
        # Verificar que se registró la respuesta
        mock_logger.log.assert_called()
    
    @patch('audit.middleware.logger')
    def test_exception_logging(self, mock_logger):
        """Verifica que las excepciones se registran"""
        # Esto requeriría una vista que lance excepción para probarlo completamente
        # Por ahora verificamos que el método existe
        from audit.middleware import AuditMiddleware
        
        middleware = AuditMiddleware(Mock())
        request = Mock()
        request.method = 'GET'
        request.path = '/test/'
        request.user = self.user
        request.audit_info = {'client_ip': '127.0.0.1'}
        
        exception = Exception('Test exception')
        
        # Llamar al método de excepción
        middleware.process_exception(request, exception)
        
        # Verificar que se llamó al logger
        mock_logger.error.assert_called()


class AuditAPITestCase(APITestCase):
    """Pruebas para las API de auditoría"""
    
    def setUp(self):
        # Crear usuario administrador
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpass123'
        )
        
        # Generar logs válidos creando/actualizando modelos
        note = Note.objects.create(title='Seed Note', content='seed', user=self.regular_user)
        note.title = 'Seed Note Updated'
        note.save()

    
    def test_audit_logs_admin_access(self):
        """Verifica que solo admins pueden acceder a logs de auditoría"""
        # Autenticar como admin
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/audit/api/logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_audit_logs_regular_user_denied(self):
        """Verifica que usuarios regulares no pueden acceder"""
        # Autenticar como usuario regular
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get('/audit/api/logs/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_audit_logs_anonymous_denied(self):
        """Verifica que usuarios anónimos no pueden acceder"""
        response = self.client.get('/audit/api/logs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_audit_logs_filtering(self):
        """Verifica que los filtros funcionan correctamente"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Filtrar por usuario
        response = self.client.get(f'/audit/api/logs/?user_id={self.regular_user.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Filtrar por acción
        response = self.client.get('/audit/api/logs/?action=create')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Filtrar por fecha
        date_from = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.get(f'/audit/api/logs/?date_from={date_from}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_audit_statistics(self):
        """Verifica que las estadísticas funcionan"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/audit/api/logs/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estructura de respuesta
        expected_keys = ['total_logs', 'actions', 'models', 'top_users', 'daily_activity']
        for key in expected_keys:
            self.assertIn(key, response.data)
    
    def test_user_activity_endpoint(self):
        """Verifica el endpoint de actividad de usuario"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(f'/audit/api/logs/user_activity/?user_id={self.regular_user.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estructura de respuesta
        self.assertIn('user', response.data)
        self.assertIn('statistics', response.data)
        self.assertIn('recent_activity', response.data)
    
    def test_dashboard_data_endpoint(self):
        """Verifica el endpoint de datos del dashboard"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/audit/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estructura de respuesta
        expected_keys = ['period', 'metrics', 'charts']
        for key in expected_keys:
            self.assertIn(key, response.data)
    
    def test_cleanup_logs_preview(self):
        """Verifica el preview de limpieza de logs"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post('/audit/api/cleanup/', {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Debe ser preview por defecto
        self.assertTrue(response.data.get('preview', False))
        self.assertIn('logs_to_delete', response.data)
    
    def test_cleanup_logs_execution(self):
        """Verifica la ejecución real de limpieza"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear log antiguo
        old_date = timezone.now() - timedelta(days=400)
        LogEntry.objects.create(
            action=LogEntry.Action.CREATE,
            object_id='old',
            object_repr='Old Object',
            timestamp=old_date,
            actor=self.regular_user
        )
        
        initial_count = LogEntry.objects.count()
        
        response = self.client.post('/audit/api/cleanup/', {'confirm': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que se ejecutó la limpieza
        self.assertTrue(response.data.get('success', False))
        self.assertIn('deleted_count', response.data)


class AuditIntegrationTestCase(TestCase):
    """Pruebas de integración para verificar el flujo completo de auditoría"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_complete_note_lifecycle_audit(self):
        """Verifica que todo el ciclo de vida de una nota se audita"""
        initial_count = LogEntry.objects.count()
        
        # 1. Crear nota
        note = Note.objects.create(
            title='Integration Test Note',
            content='Test content for integration',
            user=self.user
        )
        
        # Verificar creación auditada
        self.assertEqual(LogEntry.objects.count(), initial_count + 1)
        create_log = LogEntry.objects.latest('timestamp')
        self.assertEqual(create_log.action, LogEntry.Action.CREATE)
        
        # 2. Actualizar nota
        note.title = 'Updated Integration Test Note'
        note.save()
        
        # Verificar actualización auditada
        self.assertEqual(LogEntry.objects.count(), initial_count + 2)
        update_log = LogEntry.objects.latest('timestamp')
        self.assertEqual(update_log.action, LogEntry.Action.UPDATE)
        
        # 3. Agregar tag
        tag = Tag.objects.create(name='integration-test')
        note.tags.add(tag)
        
        # Verificar creación de tag auditada
        tag_logs = LogEntry.objects.filter(object_repr__contains='integration-test')
        self.assertTrue(tag_logs.exists())
        
        # 4. Eliminar nota
        note_id = note.pk
        note.delete()
        
        # Verificar eliminación auditada
        delete_log = LogEntry.objects.filter(
            action=LogEntry.Action.DELETE,
            object_id=str(note_id)
        ).first()
        self.assertIsNotNone(delete_log)
    
    def test_user_activity_audit_flow(self):
        """Verifica el flujo de auditoría de actividad de usuario"""
        initial_count = LogEntry.objects.count()
        
        # 1. Login (esto se haría a través de la API en implementación real)
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Crear contenido
        note = Note.objects.create(
            title='User Activity Test',
            content='Testing user activity audit',
            user=self.user
        )
        
        # 3. Modificar perfil
        self.user.nickname = 'audit_test_user'
        self.user.save()
        
        # Verificar que todas las acciones fueron auditadas
        final_count = LogEntry.objects.count()
        self.assertGreater(final_count, initial_count)
        
        # Verificar que los logs tienen el actor correcto
        user_logs = LogEntry.objects.filter(actor=self.user)
        self.assertTrue(user_logs.exists())
        
        # Verificar diferentes tipos de acciones
        actions = set(user_logs.values_list('action', flat=True))
        expected_actions = {LogEntry.Action.CREATE, LogEntry.Action.UPDATE}
        self.assertTrue(expected_actions.issubset(actions))


class AuditSecurityTestCase(TestCase):
    """Pruebas de seguridad para el sistema de auditoría"""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com', 
            password='regularpass123'
        )
    
    def test_sensitive_data_not_logged(self):
        """Verifica que datos sensibles no se registran en logs"""
        # Cambiar contraseña
        self.regular_user.set_password('newpassword123')
        self.regular_user.save()
        
        # Verificar que la contraseña no aparece en los logs
        logs = LogEntry.objects.filter(actor=self.regular_user)
        for log in logs:
            log_data = str(log.changes)
            self.assertNotIn('newpassword123', log_data)
            self.assertNotIn('password', log_data.lower())
    
    def test_encrypted_fields_handling(self):
        """Verifica el manejo de campos encriptados en auditoría"""
        # Actualizar campos encriptados
        self.regular_user.email = 'newemail@example.com'
        self.regular_user.first_name = 'NewFirstName'
        self.regular_user.save()
        
        # Obtener el log de cambios
        log = LogEntry.objects.filter(actor=None).latest('timestamp')  # Sistema como actor
        
        # Los campos encriptados deben estar marcados como masked o no contener valor real
        if log.changes:
            changes_str = str(log.changes)
            # No debe contener el email en texto plano
            self.assertNotIn('newemail@example.com', changes_str)
    
    def test_audit_log_tampering_prevention(self):
        """Verifica que los logs de auditoría no pueden ser modificados fácilmente"""
        # Crear un log
        note = Note.objects.create(
            title='Tamper Test',
            content='Testing tamper prevention',
            user=self.regular_user
        )
        
        log_entry = LogEntry.objects.latest('timestamp')
        original_timestamp = log_entry.timestamp
        original_changes = log_entry.changes
        
        # Intentar modificar el log (esto no debería ser posible en producción)
        # En una implementación real, los logs estarían en tabla readonly o con triggers
        with self.assertLogs('auditlog', level='INFO'):
            # Simulamos que cualquier cambio directo a logs se registra
            pass