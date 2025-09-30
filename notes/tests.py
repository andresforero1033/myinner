from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from notes.models import Note, Tag

User = get_user_model()


class NoteTagTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(username='userx', email='ux@test.com', password='Strong123')
		# login (session based)
		self.client.post('/api/auth/login/', {'username': 'userx', 'password': 'Strong123'}, format='json')
		self.notes_url = '/api/notes/'

	def test_create_note_with_tags_and_retrieve(self):
		payload = {
			'title': 'Primera Nota',
			'content': 'Contenido base',
			'tags': ['uno', 'dos']
		}
		resp = self.client.post(self.notes_url, payload, format='json')
		self.assertEqual(resp.status_code, 201)
		note_id = resp.data['id']
		self.assertEqual(set(resp.data['tags']), {'uno', 'dos'})
		# listar
		list_resp = self.client.get(self.notes_url)
		self.assertEqual(list_resp.status_code, 200)
		self.assertEqual(len(list_resp.data), 1)
		self.assertEqual(list_resp.data[0]['id'], note_id)

	def test_filter_by_tag(self):
		n1 = Note.objects.create(user=self.user, title='A', content='X')
		n2 = Note.objects.create(user=self.user, title='B', content='Y')
		t1 = Tag.objects.create(name='rojo')
		t2 = Tag.objects.create(name='azul')
		n1.tags.add(t1)
		n2.tags.add(t2)
		resp = self.client.get(self.notes_url + '?tag=rojo')
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(len(resp.data), 1)
		self.assertEqual(resp.data[0]['title'], 'A')

	def test_search_q(self):
		Note.objects.create(user=self.user, title='Viaje a la montaña', content='Detalles del viaje')
		Note.objects.create(user=self.user, title='Gastos', content='Presupuesto del viaje')
		resp = self.client.get(self.notes_url + '?q=viaje')
		# Debe traer ambas (título y contenido coinciden)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(len(resp.data), 2)

	def test_tags_any_case_normalization(self):
		payload = {
			'title': 'Case Tags',
			'content': 'Contenido',
			'tags': ['RoJo', '  ROJO ', 'Azul']
		}
		resp = self.client.post(self.notes_url, payload, format='json')
		self.assertEqual(resp.status_code, 201)
		# Debe deduplicar y normalizar a minúsculas
		self.assertEqual(set(resp.data['tags']), {'rojo', 'azul'})
