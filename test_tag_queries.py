"""
Script para probar el autocomplete usando Django shell
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myinner_backend.settings')
django.setup()

from notes.models import Tag
from django.db.models import Count

def test_tag_queries():
    """Probar las queries que usa el autocomplete"""
    
    print("🧪 Probando queries de autocomplete de tags...")
    
    # Query 1: Todos los tags ordenados por uso
    print("\n1️⃣ Todos los tags ordenados por uso:")
    all_tags = Tag.objects.annotate(
        usage_count=Count('notes', distinct=True)
    ).order_by('-usage_count', 'name')
    
    print(f"Total de tags: {all_tags.count()}")
    for tag in all_tags[:5]:
        print(f"  - {tag.name}: {tag.usage_count} usos")
    
    # Query 2: Filtrado por nombre
    print("\n2️⃣ Tags que contienen 'prog':")
    filtered_tags = Tag.objects.filter(
        name__icontains='prog'
    ).annotate(
        usage_count=Count('notes', distinct=True)
    ).order_by('-usage_count', 'name')
    
    print(f"Tags encontrados: {filtered_tags.count()}")
    for tag in filtered_tags:
        print(f"  - {tag.name}: {tag.usage_count} usos")
    
    # Query 3: Con límite
    print("\n3️⃣ Top 3 tags más usados:")
    top_tags = Tag.objects.annotate(
        usage_count=Count('notes', distinct=True)
    ).order_by('-usage_count', 'name')[:3]
    
    for tag in top_tags:
        print(f"  - {tag.name}: {tag.usage_count} usos")
    
    # Estadísticas generales
    print("\n📊 Estadísticas:")
    total_tags = Tag.objects.count()
    used_tags = Tag.objects.annotate(
        usage_count=Count('notes', distinct=True)
    ).filter(usage_count__gt=0).count()
    
    print(f"Total de tags: {total_tags}")
    print(f"Tags en uso: {used_tags}")
    print(f"Tags sin uso: {total_tags - used_tags}")

if __name__ == "__main__":
    test_tag_queries()