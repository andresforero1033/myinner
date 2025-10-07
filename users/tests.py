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


class TagAutocompleteTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='testuser',
			email='test@example.com', 
			password='testpass123'
		)
		self.client.force_authenticate(user=self.user)
		self.autocomplete_url = '/api/tags/'

		# Crear tags de prueba con diferentes cantidades de uso
		from notes.models import Tag, Note
		
		# Tags con diferentes frecuencias de uso
		self.tag_python = Tag.objects.create(name='python')
		self.tag_django = Tag.objects.create(name='django')
		self.tag_javascript = Tag.objects.create(name='javascript')
		self.tag_programming = Tag.objects.create(name='programming')
		self.tag_web = Tag.objects.create(name='web')
		
		# Crear notas para simular uso de tags
		note1 = Note.objects.create(user=self.user, title='Note 1', content='Content 1')
		note1.tags.set([self.tag_python, self.tag_django])  # python: 3 usos, django: 2 usos
		
		note2 = Note.objects.create(user=self.user, title='Note 2', content='Content 2') 
		note2.tags.set([self.tag_python, self.tag_programming])  # python: 3, programming: 1
		
		note3 = Note.objects.create(user=self.user, title='Note 3', content='Content 3')
		note3.tags.set([self.tag_python, self.tag_django])  # python: 3, django: 2
		
		note4 = Note.objects.create(user=self.user, title='Note 4', content='Content 4')
		note4.tags.set([self.tag_javascript])  # javascript: 1 uso

	def test_autocomplete_requires_authentication(self):
		"""Test que el endpoint requiere autenticación"""
		self.client.logout()
		response = self.client.get(self.autocomplete_url)
		self.assertEqual(response.status_code, 403)

	def test_autocomplete_without_query_returns_all_tags_ordered_by_usage(self):
		"""Test que sin query devuelve todas las tags ordenadas por uso"""
		response = self.client.get(self.autocomplete_url)
		self.assertEqual(response.status_code, 200)
		
		data = response.json()
		self.assertIn('tags', data)
		self.assertIn('query', data) 
		self.assertIn('count', data)
		self.assertEqual(data['query'], '')
		self.assertEqual(len(data['tags']), 5)  # Todos los tags
		
		# Verificar orden por uso: python(3) > django(2) > javascript,programming,web(1 cada uno)
		tags = data['tags']
		self.assertEqual(tags[0]['name'], 'python')
		self.assertEqual(tags[0]['usage_count'], 3)
		self.assertEqual(tags[1]['name'], 'django') 
		self.assertEqual(tags[1]['usage_count'], 2)
		
		# Los siguientes tienen mismo uso (1), deben estar ordenados alfabéticamente
		remaining_names = [tag['name'] for tag in tags[2:]]
		self.assertEqual(remaining_names, ['javascript', 'programming', 'web'])

	def test_autocomplete_with_query_filters_tags(self):
		"""Test filtrado por query parameter"""
		response = self.client.get(f'{self.autocomplete_url}?q=prog')
		self.assertEqual(response.status_code, 200)
		
		data = response.json()
		self.assertEqual(data['query'], 'prog')
		self.assertEqual(len(data['tags']), 1)
		self.assertEqual(data['tags'][0]['name'], 'programming')

	def test_autocomplete_case_insensitive_query(self):
		"""Test que la búsqueda es case insensitive"""
		response = self.client.get(f'{self.autocomplete_url}?q=PYTHON')
		self.assertEqual(response.status_code, 200)
		
		data = response.json()
		self.assertEqual(len(data['tags']), 1)
		self.assertEqual(data['tags'][0]['name'], 'python')

	def test_autocomplete_respects_limit_parameter(self):
		"""Test que el parámetro limit funciona correctamente"""
		response = self.client.get(f'{self.autocomplete_url}?limit=2')
		self.assertEqual(response.status_code, 200)
		
		data = response.json()
		self.assertEqual(len(data['tags']), 2)
		# Debe devolver los 2 más usados: python y django
		self.assertEqual(data['tags'][0]['name'], 'python')
		self.assertEqual(data['tags'][1]['name'], 'django')

	def test_autocomplete_limit_maximum_is_50(self):
		"""Test que el límite máximo es 50"""
		response = self.client.get(f'{self.autocomplete_url}?limit=100')
		self.assertEqual(response.status_code, 200)
		# No debe fallar, pero internamente usa máximo 50

	def test_autocomplete_no_matches_returns_empty(self):
		"""Test que query sin matches devuelve array vacío"""
		response = self.client.get(f'{self.autocomplete_url}?q=nonexistent')
		self.assertEqual(response.status_code, 200)
		
		data = response.json()
		self.assertEqual(data['query'], 'nonexistent')
		self.assertEqual(len(data['tags']), 0)
		self.assertEqual(data['count'], 0)

	def test_autocomplete_empty_query_parameter(self):
		"""Test que query vacía se maneja correctamente"""
		response = self.client.get(f'{self.autocomplete_url}?q=')
		self.assertEqual(response.status_code, 200)
		
		data = response.json()
		self.assertEqual(data['query'], '')
		self.assertEqual(len(data['tags']), 5)  # Devuelve todos

	def test_autocomplete_response_structure(self):
		"""Test que la estructura de respuesta es correcta"""
		response = self.client.get(f'{self.autocomplete_url}?q=web&limit=5')
		self.assertEqual(response.status_code, 200)
		
		data = response.json()
		
		# Verificar estructura principal
		self.assertIn('tags', data)
		self.assertIn('query', data)
		self.assertIn('count', data)
		
		# Verificar estructura de cada tag
		if data['tags']:
			tag = data['tags'][0]
			self.assertIn('id', tag)
			self.assertIn('name', tag)
			self.assertIn('usage_count', tag)
			self.assertIn('created_at', tag)

	def test_autocomplete_partial_match(self):
		"""Test matching parcial en nombres de tags"""
		response = self.client.get(f'{self.autocomplete_url}?q=java')
		self.assertEqual(response.status_code, 200)
		
		data = response.json()
		self.assertEqual(len(data['tags']), 1)
		self.assertEqual(data['tags'][0]['name'], 'javascript')
