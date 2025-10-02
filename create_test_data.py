"""
Script para crear notas de prueba y verificar paginación
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myinner_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from notes.models import Note, Tag

User = get_user_model()

def create_test_data():
    """Crear datos de prueba para verificar paginación"""
    
    # Verificar o crear usuario
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Usuario creado: {user.username}")
    else:
        print(f"✅ Usuario existente: {user.username}")
    
    # Crear tags
    tags_data = ['python', 'javascript', 'react', 'django', 'frontend', 'backend', 'api', 'database']
    tags = []
    for tag_name in tags_data:
        tag, created = Tag.objects.get_or_create(name=tag_name)
        tags.append(tag)
        if created:
            print(f"✅ Tag creado: {tag_name}")
    
    # Crear notas de prueba
    existing_count = Note.objects.filter(user=user).count()
    print(f"📝 Notas existentes: {existing_count}")
    
    if existing_count < 25:
        notes_to_create = 25 - existing_count
        print(f"🔄 Creando {notes_to_create} notas adicionales...")
        
        for i in range(notes_to_create):
            note_num = existing_count + i + 1
            
            note = Note.objects.create(
                user=user,
                title=f"Nota de Prueba #{note_num}",
                content=f"Contenido de la nota número {note_num}. "
                       f"Esta es una nota creada para probar la funcionalidad de paginación. "
                       f"Contiene información de ejemplo para verificar que los filtros y búsquedas funcionan correctamente."
            )
            
            # Añadir 1-3 tags aleatorios a cada nota
            import random
            selected_tags = random.sample(tags, random.randint(1, 3))
            note.tags.set(selected_tags)
            
            if note_num % 5 == 0:
                print(f"✅ Creadas {note_num} notas...")
    
    total_notes = Note.objects.filter(user=user).count()
    print(f"🎯 Total notas para {user.username}: {total_notes}")
    
    # Verificar configuración de paginación
    print("\n📋 Verificación de paginación:")
    print(f"- Con page_size=10: {total_notes // 10 + (1 if total_notes % 10 else 0)} páginas")
    print(f"- Con page_size=5: {total_notes // 5 + (1 if total_notes % 5 else 0)} páginas")
    
    print(f"\n🔗 URLs de prueba:")
    print(f"- http://localhost:3000/dashboard")
    print(f"- http://127.0.0.1:8000/api/notes/ (página 1)")
    print(f"- http://127.0.0.1:8000/api/notes/?page=2 (página 2)")
    print(f"- http://127.0.0.1:8000/api/notes/?page_size=5 (5 por página)")
    
    return user, total_notes

if __name__ == "__main__":
    print("🚀 Creando datos de prueba para paginación...\n")
    user, count = create_test_data()
    print(f"\n✅ Datos de prueba listos! Usuario: {user.username}, Notas: {count}")
    print("\n🎯 Ahora puedes:")
    print("1. Hacer login con: testuser / testpass123")
    print("2. Ver la paginación en funcionamiento")
    print("3. Probar diferentes page_size y filtros")