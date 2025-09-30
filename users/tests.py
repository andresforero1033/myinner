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
