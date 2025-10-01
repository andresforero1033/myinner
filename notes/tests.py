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

	def test_user_cannot_access_other_user_notes(self):
		# Crear segundo usuario y nota
		other_user = User.objects.create_user(username='otheruser', email='other@test.com', password='Pass123')
		other_note = Note.objects.create(
			user=other_user,
			title='Nota Privada',
			content='Solo para other_user'
		)
		
		# Intentar acceder a nota de otro usuario (GET)
		resp = self.client.get(f'/api/notes/{other_note.id}/')
		self.assertIn(resp.status_code, (403, 404))  # Forbidden o Not Found
		
		# Intentar editar nota de otro usuario (PUT)
		update_payload = {'title': 'Nota Hackeada', 'content': 'Contenido modificado'}
		resp = self.client.put(f'/api/notes/{other_note.id}/', update_payload, format='json')
		self.assertIn(resp.status_code, (403, 404))
		
		# Verificar que la nota original no se modificó
		other_note.refresh_from_db()
		self.assertEqual(other_note.title, 'Nota Privada')
		
		# Verificar que el usuario solo ve sus propias notas en listado
		Note.objects.create(user=self.user, title='Mi Nota', content='Mi contenido')
		list_resp = self.client.get(self.notes_url)
		self.assertEqual(list_resp.status_code, 200)
		# Solo debe ver su propia nota, no la de other_user
		titles = [note['title'] for note in list_resp.data]
		self.assertIn('Mi Nota', titles)
		self.assertNotIn('Nota Privada', titles)

	def test_create_note_without_tags(self):
		# Crear nota con lista de tags vacía
		payload = {
			'title': 'Nota Sin Tags',
			'content': 'Esta nota no tiene etiquetas',
			'tags': []
		}
		resp = self.client.post(self.notes_url, payload, format='json')
		self.assertEqual(resp.status_code, 201)
		self.assertEqual(resp.data['title'], 'Nota Sin Tags')
		self.assertEqual(resp.data['tags'], [])
		
		# Verificar en base de datos
		note = Note.objects.get(id=resp.data['id'])
		self.assertEqual(note.tags.count(), 0)
		
		# Crear nota sin especificar campo tags (debería funcionar igual)
		payload_no_tags = {
			'title': 'Otra Nota Sin Tags',
			'content': 'Campo tags omitido'
		}
		resp2 = self.client.post(self.notes_url, payload_no_tags, format='json')
		self.assertEqual(resp2.status_code, 201)
		self.assertEqual(resp2.data['tags'], [])
