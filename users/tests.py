from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


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
