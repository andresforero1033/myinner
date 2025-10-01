from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
# TODO: Para verificación de email (cuando se implemente):
# from django.core import mail
# from django.utils import timezone
# from datetime import timedelta


User = get_user_model()


class AuthTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.register_url = '/api/auth/register/'
		self.login_url = '/api/auth/login/'
		self.me_url = '/api/auth/me/'

	def test_register_creates_user_and_prefs(self):
		payload = {
			'username': 'user1',
			'email': 'user1@example.com',
			'password': 'StrongPass123',
			'password2': 'StrongPass123'
		}
		resp = self.client.post(self.register_url, payload, format='json')
		self.assertEqual(resp.status_code, 201)
		self.assertTrue(User.objects.filter(username='user1').exists())

	def test_login_with_username(self):
		User.objects.create_user(username='alpha', email='alpha@test.com', password='MyPass123')
		resp = self.client.post(self.login_url, {'username': 'alpha', 'password': 'MyPass123'}, format='json')
		self.assertEqual(resp.status_code, 200)
		# sesión establecida -> /auth/me debe devolver autenticado
		me = self.client.get(self.me_url)
		self.assertEqual(me.status_code, 200)
		self.assertEqual(me.data['username'], 'alpha')

	def test_login_with_email(self):
		User.objects.create_user(username='beta', email='beta@test.com', password='MyPass123')
		resp = self.client.post(self.login_url, {'username': 'beta@test.com', 'password': 'MyPass123'}, format='json')
		self.assertEqual(resp.status_code, 200)
		me = self.client.get(self.me_url)
		self.assertEqual(me.status_code, 200)
		self.assertEqual(me.data['username'], 'beta')

	def test_login_invalid_credentials(self):
		User.objects.create_user(username='gamma', email='g@test.com', password='MyPass123')
		resp = self.client.post(self.login_url, {'username': 'gamma', 'password': 'bad'}, format='json')
		self.assertEqual(resp.status_code, 400)
		# asegurar no autenticado
		me = self.client.get(self.me_url)
		# Dependiendo de middleware/CSRF puede devolver 403 al no tener sesión válida
		self.assertIn(me.status_code, (401, 403))

	def test_update_profile_username_email(self):
		# Crear usuario y autenticar
		user = User.objects.create_user(username='olduser', email='old@test.com', password='Pass123')
		self.client.post(self.login_url, {'username': 'olduser', 'password': 'Pass123'}, format='json')
		
		# Actualizar username y email (usando multipart para coincidir con ProfileView parsers)
		update_payload = {
			'username': 'newuser',
			'email': 'new@test.com'
		}
		resp = self.client.patch('/api/profile/', update_payload)  # Sin format='json'
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.data['username'], 'newuser')
		self.assertEqual(resp.data['email'], 'new@test.com')
		
		# Verificar en base de datos
		user.refresh_from_db()
		self.assertEqual(user.username, 'newuser')
		self.assertEqual(user.email, 'new@test.com')
		
		# Verificar que el usuario puede hacer login con nuevo username
		self.client.post('/api/auth/logout/', format='json')
		login_resp = self.client.post(self.login_url, {'username': 'newuser', 'password': 'Pass123'}, format='json')
		self.assertEqual(login_resp.status_code, 200)


class EmailVerificationTests(TestCase):
	"""
	Pruebas para verificación de email.
	
	Esquema de implementación futura:
	- Modelo: EmailVerificationToken (user, token, created_at, is_used)
	- Endpoints: /auth/verify-email/, /auth/resend-verification/
	- Email backend: configurar SMTP o servicio como SendGrid
	- Frontend: Página de verificación con token desde URL
	"""
	
	def setUp(self):
		self.client = APIClient()
		self.register_url = '/api/auth/register/'
		self.verify_url = '/api/auth/verify-email/'  # TODO: crear endpoint
		self.resend_url = '/api/auth/resend-verification/'  # TODO: crear endpoint
	
	def test_registration_sends_verification_email(self):
		"""
		TODO: Al registrarse, verificar que:
		- Usuario creado con is_email_verified=False
		- Token de verificación generado
		- Email enviado (usar django.core.mail.outbox en tests)
		"""
		self.skipTest("Pendiente implementar sistema de verificación de email")
	
	def test_valid_token_verifies_email(self):
		"""
		TODO: Con token válido:
		- POST /auth/verify-email/ con token en body
		- Usuario.is_email_verified cambia a True
		- Token marcado como usado
		- Respuesta 200 con mensaje de éxito
		"""
		self.skipTest("Pendiente implementar sistema de verificación de email")
	
	def test_invalid_or_expired_token(self):
		"""
		TODO: Casos de error:
		- Token inexistente: 400 'Token inválido'
		- Token ya usado: 400 'Token ya utilizado'
		- Token expirado (>24h): 400 'Token expirado'
		- Token malformado: 400 'Formato inválido'
		"""
		self.skipTest("Pendiente implementar sistema de verificación de email")
	
	def test_resend_verification_email(self):
		"""
		TODO: Para usuario no verificado:
		- POST /auth/resend-verification/ con email
		- Invalidar tokens anteriores
		- Generar nuevo token
		- Enviar nuevo email
		- Rate limiting (máx 3 por hora)
		"""
		self.skipTest("Pendiente implementar sistema de verificación de email")
	
	def test_already_verified_user_cannot_reverify(self):
		"""
		TODO: Si usuario ya verificado intenta usar token:
		- Respuesta 400 'Email ya verificado'
		- No cambiar estado del usuario
		"""
		self.skipTest("Pendiente implementar sistema de verificación de email")
	
	def test_verification_status_in_profile(self):
		"""
		TODO: GET /auth/me/ debe incluir campo 'is_email_verified'
		para que frontend muestre estado y botón de reenviar si necesario
		"""
		self.skipTest("Pendiente implementar sistema de verificación de email")
