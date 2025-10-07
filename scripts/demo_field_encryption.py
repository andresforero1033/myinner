#!/usr/bin/env python
"""
Demostración de Encriptación de Campos - MyInner

Este script demuestra cómo funciona la encriptación transparente de campos
en los modelos Note y CustomUser.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myinner_backend.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model
from notes.models import Note

User = get_user_model()


def demonstrate_user_encryption():
    """Demuestra la encriptación de datos de usuario"""
    print("=" * 60)
    print("DEMOSTRACIÓN: Encriptación de Datos de Usuario")
    print("=" * 60)
    
    # Crear usuario con datos sensibles
    user = User.objects.create_user(
        username='demo_user',
        email='sensitive.email@empresa.com',
        first_name='María Elena',
        last_name='García Rodríguez',
        password='secure_password123'
    )
    
    print(f"✅ Usuario creado: {user.username}")
    print(f"📧 Email (desencriptado): {user.email}")
    print(f"👤 Nombre completo (desencriptado): {user.first_name} {user.last_name}")
    
    # Mostrar cómo se ven los datos encriptados en la base de datos
    print("\n🔐 Datos como se almacenan en la base de datos (encriptados):")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT email, first_name, last_name FROM users_customuser WHERE username = %s",
            [user.username]
        )
        row = cursor.fetchone()
        
        print(f"   Email encriptado: {row[0][:50]}...")
        print(f"   Nombre encriptado: {row[1][:50]}...")
        print(f"   Apellido encriptado: {row[2][:50]}...")
    
    print(f"\n📊 Longitud de datos:")
    print(f"   Email original: {len(user.email)} caracteres")
    print(f"   Email encriptado: {len(row[0])} caracteres")
    print(f"   Nombre original: {len(user.first_name)} caracteres")
    print(f"   Nombre encriptado: {len(row[1])} caracteres")
    
    return user


def demonstrate_note_encryption(user):
    """Demuestra la encriptación de contenido de notas"""
    print("\n" + "=" * 60)
    print("DEMOSTRACIÓN: Encriptación de Contenido de Notas")
    print("=" * 60)
    
    # Crear nota con contenido sensible
    sensitive_content = """
    Información médica personal:
    - Presión arterial: 120/80
    - Medicamentos: Aspirina 100mg diaria
    - Alergias: Penicilina
    - Próxima cita: Dr. López - 15/Dic/2024
    
    Datos financieros:
    - Cuenta de ahorros: ****-1234
    - Inversiones: $50,000 en fondos
    - Meta ahorro 2024: $12,000
    """
    
    note = Note.objects.create(
        title='Información Personal Sensible',
        content=sensitive_content.strip(),
        user=user
    )
    
    print(f"✅ Nota creada: {note.title}")
    print(f"📝 Contenido (desencriptado):")
    print(f"   {note.content[:100]}...")
    
    # Mostrar cómo se ve el contenido encriptado en la base de datos
    print("\n🔐 Contenido como se almacena en la base de datos (encriptado):")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT content FROM notes_note WHERE id = %s",
            [note.id]
        )
        row = cursor.fetchone()
        
        encrypted_content = row[0]
        print(f"   Contenido encriptado: {encrypted_content[:100]}...")
    
    print(f"\n📊 Longitud de contenido:")
    print(f"   Contenido original: {len(note.content)} caracteres")
    print(f"   Contenido encriptado: {len(encrypted_content)} caracteres")
    print(f"   Overhead de encriptación: {len(encrypted_content) - len(note.content)} caracteres")
    
    return note


def demonstrate_query_functionality(user):
    """Demuestra las capacidades y limitaciones de consultas"""
    print("\n" + "=" * 60)
    print("DEMOSTRACIÓN: Consultas con Campos Encriptados")
    print("=" * 60)
    
    # Crear usuarios adicionales para pruebas
    user2 = User.objects.create_user(
        username='demo_user2',
        email='otro.email@empresa.com',
        first_name='Carlos',
        last_name='Mendoza',
        password='password456'
    )
    
    print("✅ Usuarios de prueba creados")
    
    # Consultas que funcionan bien
    print("\n🔍 Consultas por campos NO encriptados:")
    found_user = User.objects.filter(username='demo_user').first()
    print(f"   Búsqueda por username: {found_user.username if found_user else 'No encontrado'}")
    
    # Listar todos los usuarios
    print("\n📋 Todos los usuarios (datos desencriptados automáticamente):")
    for u in User.objects.all().order_by('username'):
        if u.username.startswith('demo_'):
            print(f"   👤 {u.username}: {u.email} - {u.first_name} {u.last_name}")
    
    # Nota sobre limitaciones
    print("\n⚠️  LIMITACIONES de búsquedas en campos encriptados:")
    print("   - No se pueden usar: __icontains, __startswith, __endswith")
    print("   - Búsquedas case-insensitive pueden no funcionar")
    print("   - Ordenamiento por campos encriptados no es significativo")
    
    # Cleanup
    user2.delete()


def demonstrate_update_functionality(user, note):
    """Demuestra actualizaciones de campos encriptados"""
    print("\n" + "=" * 60)
    print("DEMOSTRACIÓN: Actualización de Campos Encriptados")
    print("=" * 60)
    
    # Actualizar datos del usuario
    original_email = user.email
    original_name = user.first_name
    
    user.email = 'nuevo.email@empresa.com'
    user.first_name = 'María Elena Actualizada'
    user.save()
    
    print(f"✅ Usuario actualizado:")
    print(f"   Email: {original_email} → {user.email}")
    print(f"   Nombre: {original_name} → {user.first_name}")
    
    # Actualizar contenido de la nota
    original_content_preview = note.content[:50]
    note.content = "Contenido actualizado con nueva información médica sensible: Análisis de sangre pendiente para enero 2024."
    note.save()
    
    print(f"\n✅ Nota actualizada:")
    print(f"   Contenido anterior: {original_content_preview}...")
    print(f"   Contenido nuevo: {note.content[:50]}...")
    
    # Verificar que los nuevos datos también están encriptados
    print("\n🔐 Verificando que los datos actualizados están encriptados:")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT email, first_name FROM users_customuser WHERE username = %s",
            [user.username]
        )
        user_row = cursor.fetchone()
        
        cursor.execute(
            "SELECT content FROM notes_note WHERE id = %s",
            [note.id]
        )
        note_row = cursor.fetchone()
        
        print(f"   ✓ Email actualizado está encriptado: {user_row[0] != user.email}")
        print(f"   ✓ Nombre actualizado está encriptado: {user_row[1] != user.first_name}")
        print(f"   ✓ Contenido actualizado está encriptado: {note_row[0] != note.content}")


def cleanup_demo_data():
    """Limpia los datos de demostración"""
    print("\n" + "=" * 60)
    print("LIMPIEZA: Eliminando datos de demostración")
    print("=" * 60)
    
    # Eliminar notas de demo
    demo_notes = Note.objects.filter(user__username__startswith='demo_')
    notes_count = demo_notes.count()
    demo_notes.delete()
    
    # Eliminar usuarios de demo
    demo_users = User.objects.filter(username__startswith='demo_')
    users_count = demo_users.count()
    demo_users.delete()
    
    print(f"✅ Limpieza completada:")
    print(f"   📝 {notes_count} notas eliminadas")
    print(f"   👤 {users_count} usuarios eliminados")


def main():
    """Función principal de demostración"""
    print("🚀 INICIANDO DEMOSTRACIÓN DE ENCRIPTACIÓN DE CAMPOS")
    print("Este script muestra cómo MyInner protege datos sensibles automáticamente")
    
    try:
        # Ejecutar demostraciones
        user = demonstrate_user_encryption()
        note = demonstrate_note_encryption(user)
        demonstrate_query_functionality(user)
        demonstrate_update_functionality(user, note)
        
        print("\n" + "=" * 60)
        print("✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("🔐 Resumen de seguridad:")
        print("   ✓ Los datos sensibles se encriptan automáticamente")
        print("   ✓ Los datos se desencriptan transparentemente al acceder")
        print("   ✓ Las actualizaciones mantienen la encriptación")
        print("   ✓ Los datos están protegidos en la base de datos")
        print("\n🎯 Beneficios clave:")
        print("   • Protección contra dumps de base de datos")
        print("   • Transparencia total para desarrolladores")
        print("   • Cumplimiento de regulaciones de privacidad")
        print("   • Seguridad sin impacto en la funcionalidad")
        
    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")
        print("Verifica que:")
        print("   • La clave FIELD_ENCRYPTION_KEY esté configurada")
        print("   • Las migraciones estén aplicadas")
        print("   • Las dependencias estén instaladas")
    
    finally:
        # Limpiar datos de demostración
        cleanup_demo_data()


if __name__ == '__main__':
    main()