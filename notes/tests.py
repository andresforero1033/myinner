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
		self.assertEqual(list_resp.data['count'], 1)
		self.assertEqual(len(list_resp.data['results']), 1)
		self.assertEqual(list_resp.data['results'][0]['id'], note_id)

	def test_filter_by_tag(self):
		n1 = Note.objects.create(user=self.user, title='A', content='X')
		n2 = Note.objects.create(user=self.user, title='B', content='Y')
		t1 = Tag.objects.create(name='rojo')
		t2 = Tag.objects.create(name='azul')
		n1.tags.add(t1)
		n2.tags.add(t2)
		resp = self.client.get(self.notes_url + '?tag=rojo')
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.data['count'], 1)
		self.assertEqual(len(resp.data['results']), 1)
		self.assertEqual(resp.data['results'][0]['title'], 'A')

	def test_search_q(self):
		Note.objects.create(user=self.user, title='Viaje a la montaña', content='Detalles del viaje')
		Note.objects.create(user=self.user, title='Gastos', content='Presupuesto del viaje')
		resp = self.client.get(self.notes_url + '?q=viaje')
		# Debe traer ambas (título y contenido coinciden)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.data['count'], 2)
		self.assertEqual(len(resp.data['results']), 2)

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
		titles = [note['title'] for note in list_resp.data['results']]
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


class PaginationTests(TestCase):
	"""
	Pruebas para paginación de notas.
	
	Esquema de implementación futura:
	- Backend: Añadir PageNumberPagination en settings/views
	- Frontend: Componente Pagination con botones prev/next
	- Tests: Validar page_size, links, navegación, edge cases
	"""
	
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(username='paguser', email='pag@test.com', password='Pass123')
		self.client.post('/api/auth/login/', {'username': 'paguser', 'password': 'Pass123'}, format='json')
		self.notes_url = '/api/notes/'
	
	def test_paginated_response_structure(self):
		"""
		Verificar estructura de respuesta paginada:
		- count: total de elementos
		- next: URL página siguiente (o null)
		- previous: URL página anterior (o null)  
		- results: array de notas
		"""
		# Crear una nota para tener contenido
		Note.objects.create(user=self.user, title='Test Note', content='Content')
		resp = self.client.get(self.notes_url)
		self.assertEqual(resp.status_code, 200)
		
		# Verificar estructura paginada
		self.assertIn('count', resp.data)
		self.assertIn('next', resp.data)
		self.assertIn('previous', resp.data)
		self.assertIn('results', resp.data)
		self.assertIsInstance(resp.data['results'], list)
		self.assertEqual(resp.data['count'], 1)
		self.assertIsNone(resp.data['next'])  # Solo 1 página
		self.assertIsNone(resp.data['previous'])  # Primera página
	
	def test_page_size_limit(self):
		"""
		Crear 25 notas, verificar que page_size=10 devuelve 10 items
		y que existen 3 páginas (count=25, 10+10+5)
		"""
		# Crear 25 notas
		for i in range(25):
			Note.objects.create(user=self.user, title=f'Note {i+1}', content=f'Content {i+1}')
		
		# Primera página (por defecto page_size=10)
		resp = self.client.get(self.notes_url)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.data['count'], 25)
		self.assertEqual(len(resp.data['results']), 10)
		self.assertIsNotNone(resp.data['next'])
		self.assertIsNone(resp.data['previous'])
		
		# Verificar page_size personalizado
		resp = self.client.get(self.notes_url + '?page_size=5')
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(len(resp.data['results']), 5)
		self.assertEqual(resp.data['count'], 25)
	
	def test_navigation_links(self):
		"""
		Verificar que next/previous links funcionan correctamente:
		- Página 1: previous=null, next!=null
		- Página intermedia: ambos != null
		- Última página: next=null, previous!=null
		"""
		# Crear 25 notas para tener múltiples páginas
		for i in range(25):
			Note.objects.create(user=self.user, title=f'Note {i+1}', content=f'Content {i+1}')
		
		# Primera página
		resp1 = self.client.get(self.notes_url + '?page=1')
		self.assertEqual(resp1.status_code, 200)
		self.assertIsNone(resp1.data['previous'])
		self.assertIsNotNone(resp1.data['next'])
		
		# Página intermedia
		resp2 = self.client.get(self.notes_url + '?page=2')
		self.assertEqual(resp2.status_code, 200)
		self.assertIsNotNone(resp2.data['previous'])
		self.assertIsNotNone(resp2.data['next'])
		
		# Última página
		resp3 = self.client.get(self.notes_url + '?page=3')
		self.assertEqual(resp3.status_code, 200)
		self.assertIsNotNone(resp3.data['previous'])
		self.assertIsNone(resp3.data['next'])
	
	def test_pagination_with_search_and_filters(self):
		"""
		Verificar que paginación funciona con ?q= y ?tag=
		contando solo resultados filtrados
		"""
		# Crear notas con diferentes palabras y tags
		tag1 = Tag.objects.create(name='python')
		tag2 = Tag.objects.create(name='django')
		
		for i in range(15):
			note = Note.objects.create(user=self.user, title=f'Python note {i+1}', content='Content')
			note.tags.add(tag1)
		
		for i in range(5):
			note = Note.objects.create(user=self.user, title=f'Django note {i+1}', content='Content')
			note.tags.add(tag2)
		
		# Paginación con búsqueda
		resp = self.client.get(self.notes_url + '?q=python&page_size=5')
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.data['count'], 15)  # Solo notas con 'python'
		self.assertEqual(len(resp.data['results']), 5)
		
		# Paginación con tag
		resp = self.client.get(self.notes_url + '?tag=django&page_size=3')
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.data['count'], 5)  # Solo notas con tag django
		self.assertEqual(len(resp.data['results']), 3)
	
	def test_invalid_page_numbers(self):
		"""
		Manejar casos edge:
		- ?page=0 o negativo
		- ?page=999999 (mayor al máximo)
		- ?page=abc (no numérico)
		"""
		# Crear algunas notas para tener contenido
		for i in range(5):
			Note.objects.create(user=self.user, title=f'Note {i+1}', content='Content')
		
		# Página 0 o negativa - DRF devuelve 404
		resp = self.client.get(self.notes_url + '?page=0')
		self.assertEqual(resp.status_code, 404)
		
		resp = self.client.get(self.notes_url + '?page=-1')
		self.assertEqual(resp.status_code, 404)
		
		# Página mayor al máximo - DRF devuelve 404
		resp = self.client.get(self.notes_url + '?page=999999')
		self.assertEqual(resp.status_code, 404)
		
		# Página no numérica - DRF devuelve 404
		resp = self.client.get(self.notes_url + '?page=abc')
		self.assertEqual(resp.status_code, 404)
		
		# page_size mayor al máximo permitido (50) - debe limitarse
		resp = self.client.get(self.notes_url + '?page_size=100')
		self.assertEqual(resp.status_code, 200)
		# Debería limitarse al max_page_size=50, pero solo tenemos 5 notas
		self.assertEqual(len(resp.data['results']), 5)
