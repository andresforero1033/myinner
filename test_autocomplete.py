"""
Script para probar el endpoint de autocomplete de tags
"""
import requests
import json

def test_tag_autocomplete():
    base_url = "http://127.0.0.1:8000/api"
    
    print("🧪 Probando endpoint de autocomplete de tags...")
    
    # Test 1: Sin query (debería devolver todos los tags)
    print("\n1️⃣ Test sin query:")
    response = requests.get(f"{base_url}/tags/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Resultado: {len(data.get('tags', []))} tags encontrados")
        for tag in data.get('tags', [])[:3]:  # Mostrar primeros 3
            print(f"  - {tag['name']} ({tag['usage_count']} usos)")
    else:
        print(f"Error: {response.text}")
    
    # Test 2: Con query específica
    print("\n2️⃣ Test con query 'python':")
    response = requests.get(f"{base_url}/tags/?q=python&limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Query: '{data.get('query', '')}' - {data.get('count', 0)} resultados")
        for tag in data.get('tags', []):
            print(f"  - {tag['name']} ({tag['usage_count']} usos)")
    else:
        print(f"Error: {response.text}")
    
    # Test 3: Query sin resultados
    print("\n3️⃣ Test con query sin resultados:")
    response = requests.get(f"{base_url}/tags/?q=nonexistent")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Query: '{data.get('query', '')}' - {data.get('count', 0)} resultados")
        print(f"Tags: {data.get('tags', [])}")
    else:
        print(f"Error: {response.text}")
    
    # Test 4: Con límite
    print("\n4️⃣ Test con límite pequeño:")
    response = requests.get(f"{base_url}/tags/?limit=3")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Límite aplicado: {len(data.get('tags', []))} tags (máximo 3)")
        for tag in data.get('tags', []):
            print(f"  - {tag['name']} ({tag['usage_count']} usos)")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_tag_autocomplete()