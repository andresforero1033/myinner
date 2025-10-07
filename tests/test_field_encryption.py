"""
Pruebas para verificar la funcionalidad de encriptación de campos
"""
from django.test import TestCase
from django.db import connection
from django.contrib.auth import get_user_model
from notes.models import Note

User = get_user_model()


class FieldEncryptionTestCase(TestCase):
    """Pruebas para verificar que los campos sensibles se encriptan correctamente"""
    
    def test_user_email_encryption(self):
        """Verifica que el email se encripta en la base de datos pero se desencripta al acceder"""
        # Crear usuario con email sensible
        user = User.objects.create_user(
            username='testuser',
            email='sensitive@example.com',
            first_name='Juan',
            last_name='Pérez',
            password='testpass123'
        )
        
        # Verificar que el email se desencripta correctamente al acceder vía ORM
        self.assertEqual(user.email, 'sensitive@example.com')
        self.assertEqual(user.first_name, 'Juan')
        self.assertEqual(user.last_name, 'Pérez')
        
        # Verificar que los datos están encriptados en la base de datos
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT email, first_name, last_name FROM users_customuser WHERE username = %s",
                [user.username]
            )
            row = cursor.fetchone()
            
            # Los datos encriptados NO deben ser iguales a los originales
            self.assertNotEqual(row[0], 'sensitive@example.com')
            self.assertNotEqual(row[1], 'Juan')
            self.assertNotEqual(row[2], 'Pérez')
            
            # Los datos encriptados deben contener texto base64-like
            self.assertTrue(len(row[0]) > len('sensitive@example.com'))
            self.assertTrue(len(row[1]) > len('Juan'))
            self.assertTrue(len(row[2]) > len('Pérez'))
    
    def test_note_content_encryption(self):
        """Verifica que el contenido de las notas se encripta correctamente"""
        # Crear usuario para asociar la nota
        user = User.objects.create_user(
            username='noteuser',
            email='user@example.com',
            password='testpass123'
        )
        
        # Crear nota con contenido sensible
        sensitive_content = "Esta es información personal muy sensible que debe estar encriptada"
        note = Note.objects.create(
            title='Nota de Prueba',
            content=sensitive_content,
            user=user
        )
        
        # Verificar que el contenido se desencripta correctamente al acceder vía ORM
        self.assertEqual(note.content, sensitive_content)
        
        # Verificar que el contenido está encriptado en la base de datos
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT content FROM notes_note WHERE id = %s",
                [note.id]
            )
            row = cursor.fetchone()
            
            # El contenido encriptado NO debe ser igual al original
            self.assertNotEqual(row[0], sensitive_content)
            
            # El contenido encriptado debe ser más largo (incluye metadatos de encriptación)
            self.assertTrue(len(row[0]) > len(sensitive_content))
    
    def test_encrypted_field_queries(self):
        """Verifica que las consultas funcionan correctamente con campos encriptados"""
        # Crear usuarios de prueba
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            first_name='Ana',
            password='pass123'
        )
        
        user2 = User.objects.create_user(
            username='user2', 
            email='user2@example.com',
            first_name='Carlos',
            password='pass123'
        )
        
        # NOTA: Las búsquedas en campos encriptados pueden tener limitaciones
        # Verificar que los usuarios se pueden acceder por ID o campos no encriptados
        found_user = User.objects.filter(username='user1').first()
        self.assertEqual(found_user.email, 'user1@example.com')
        self.assertEqual(found_user.first_name, 'Ana')
        
        # Verificar conteo total
        total_users = User.objects.all().count()
        self.assertEqual(total_users, 2)
        
        # Verificar que los datos se desencriptan correctamente al iterar
        all_users = User.objects.all()
        emails = [user.email for user in all_users]
        names = [user.first_name for user in all_users]
        
        self.assertIn('user1@example.com', emails)
        self.assertIn('user2@example.com', emails)
        self.assertIn('Ana', names)
        self.assertIn('Carlos', names)
    
    def test_encrypted_field_updates(self):
        """Verifica que las actualizaciones de campos encriptados funcionan correctamente"""
        # Crear usuario
        user = User.objects.create_user(
            username='updateuser',
            email='original@example.com',
            first_name='Original',
            password='pass123'
        )
        
        # Actualizar campos encriptados
        user.email = 'updated@example.com'
        user.first_name = 'Updated'
        user.save()
        
        # Verificar que los cambios se guardaron correctamente
        updated_user = User.objects.get(username='updateuser')
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.first_name, 'Updated')
        
        # Verificar que los datos están encriptados en la BD
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT email, first_name FROM users_customuser WHERE username = %s",
                ['updateuser']
            )
            row = cursor.fetchone()
            
            # Los nuevos datos también deben estar encriptados
            self.assertNotEqual(row[0], 'updated@example.com')
            self.assertNotEqual(row[1], 'Updated')
    
    def test_note_content_updates(self):
        """Verifica que las actualizaciones del contenido de notas se encriptan"""
        # Crear usuario y nota
        user = User.objects.create_user(
            username='noteowner',
            email='owner@example.com',
            password='pass123'
        )
        
        note = Note.objects.create(
            title='Nota Actualizable',
            content='Contenido original',
            user=user
        )
        
        # Actualizar contenido
        new_content = 'Contenido actualizado con información sensible'
        note.content = new_content
        note.save()
        
        # Verificar que el nuevo contenido se desencripta correctamente
        updated_note = Note.objects.get(id=note.id)
        self.assertEqual(updated_note.content, new_content)
        
        # Verificar que está encriptado en la BD
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT content FROM notes_note WHERE id = %s",
                [note.id]
            )
            row = cursor.fetchone()
            self.assertNotEqual(row[0], new_content)