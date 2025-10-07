"""
Test simple de conectividad frontend-backend
"""
import urllib.request
import urllib.error
import json

def make_request(url):
    """Helper para hacer requests con urllib"""
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.getcode(), response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8') if e.code else ""
    except urllib.error.URLError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)

def test_connectivity():
    backend_url = "http://127.0.0.1:8000"
    
    print("🔍 Probando conectividad con el backend...")
    
    # Test 1: Health check
    print("\n1️⃣ Health Check:")
    status, content = make_request(f"{backend_url}/api/health/")
    print(f"Status: {status}")
    if status == 200:
        print("✅ Backend funcionando correctamente")
    elif status is None:
        print("❌ No se puede conectar al backend en http://127.0.0.1:8000")
        print("   Verifica que Django esté corriendo con: python manage.py runserver")
        return False
    else:
        print(f"❌ Error: {content}")
        
    # Test 2: API Root
    print("\n2️⃣ API Root:")
    status, content = make_request(f"{backend_url}/api/")
    print(f"Status: {status}")
    if status == 200:
        try:
            data = json.loads(content)
            print(f"✅ Endpoints disponibles: {len(data)} encontrados")
            if 'tags' in data:
                print("✅ Endpoint de tags disponible")
                print(f"   URL: {data['tags']}")
            else:
                print("❌ Endpoint de tags NO encontrado")
        except json.JSONDecodeError:
            print("❌ Respuesta no es JSON válido")
    else:
        print(f"❌ Error: {content}")
        
    # Test 3: Tags endpoint (sin autenticación)
    print("\n3️⃣ Tags Endpoint:")
    status, content = make_request(f"{backend_url}/api/tags/")
    print(f"Status: {status}")
    if status == 401 or status == 403:
        print("✅ Endpoint requiere autenticación (comportamiento esperado)")
    elif status == 200:
        print("⚠️ Endpoint no requiere autenticación (verificar configuración)")
    else:
        print(f"❌ Respuesta inesperada: {content}")
    
    # Test 4: Frontend check
    print("\n4️⃣ Frontend Check:")
    frontend_ports = [3000, 3001, 3002]
    frontend_running = False
    
    for port in frontend_ports:
        status, content = make_request(f"http://localhost:{port}")
        if status == 200:
            print(f"✅ Frontend encontrado en puerto {port}")
            frontend_running = True
            break
    
    if not frontend_running:
        print("❌ Frontend no encontrado en puertos 3000-3002")
        print("   Inicia con: cd frontend && npm start")
    
    print(f"\n🎯 Resumen de conectividad:")
    print(f"   Backend: {'✅' if status != None else '❌'} http://127.0.0.1:8000")
    print(f"   Frontend: {'✅' if frontend_running else '❌'} http://localhost:300X")
    
    return status is not None

if __name__ == "__main__":
    test_connectivity()