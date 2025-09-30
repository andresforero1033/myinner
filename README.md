# Myinner

Aplicación web de diario personal (Full Stack) construida con:

- Backend: Django 5, Django REST Framework, SQLite (por defecto)
- Frontend: React (Create React App), Axios, React Router, Bootstrap 5
- Autenticación: Sesiones (login/logout), usuario personalizado
- Preferencias: Tema (light/dark) y color primario persistidos en backend
- Notas: CRUD completo con filtros (más recientes, más antiguas, alfabético)
- Etiquetas: Asigna etiquetas libres a cada nota y filtra por ellas

## 1. Requisitos Previos

- Python 3.11+ instalado
- Node.js 18+ y npm

## 2. Instalación Backend

```bash
cd myinner
python -m venv venv
venv\Scripts\activate  # En Windows PowerShell
pip install -r requirements.txt  # Si existe; si no:
pip install django djangorestframework django-cors-headers pillow
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

El backend corre en: http://127.0.0.1:8000/

## 3. Instalación Frontend

```bash
cd frontend
npm install
npm start
```

El frontend corre en: http://localhost:3000/

## 4. Endpoints Principales (prefijo /api/)

- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET/PUT /api/profile
- GET/PUT /api/preferences
- GET /api/auth/me  (estado de sesión actual)
- GET/POST /api/notes?ordering=newest|oldest|alpha
- GET /api/notes?q=<texto>&order=<alpha|oldest|newest>
- GET/PUT/PATCH/DELETE /api/notes/<id>

Autenticación basada en sesión (usar withCredentials en frontend Axios ya configurado).

## 5. Modelo de Datos (Resumen)

CustomUser:
- email (login), first_name, last_name, nickname, age, gender, profile_image

UserPreference:
- user (OneToOne), theme (light/dark), primary_color

Note:
- user (FK), title, content, created_at, updated_at, tags (ManyToMany Tag)

Tag:
- name (único, normalizado a minúsculas), created_at

## 6. Flujo de Uso
1. Registrar usuario
2. Iniciar sesión
3. Crear notas (puedes añadir etiquetas en el formulario separadas por comas)
4. Clic en una etiqueta existente (#ejemplo) para filtrar por esa etiqueta
5. Puedes acumular varias: ?tag=work,ideas (UI añade chips de filtro)
6. Cambiar tema / color en Perfil
7. Filtrar notas por orden o búsqueda + etiquetas

## 7. Variables de Tema
Archivo frontend/src/theme.css controla variables CSS:
- --primary-color
- --bg-color / --text-color (según modo light/dark)

## 8. Ajustes Clave (settings.py)
- LANGUAGE_CODE = 'es'
- TIME_ZONE = 'America/Mexico_City'
- CORS_ALLOWED_ORIGINS incluye http://localhost:3000
- AUTH_USER_MODEL = 'users.CustomUser'

## 9. Ejecutar Pruebas Manuales Rápidas
Backend:
```bash
python manage.py shell -c "from users.models import CustomUser; print(CustomUser.objects.count())"
```
Frontend: Registrar, crear nota, cambiar tema, refrescar y verificar persistencia.

## 10. Migrar a MySQL (Opcional)
1. Instalar mysqlclient
2. Ajustar DATABASES en settings.py
3. Ejecutar migrate

## 11. Búsqueda y Filtros

Parámetros soportados en /api/notes/:

- q=<texto> busca en título o contenido (icontains)
- order=alpha | oldest | newest (por defecto newest)
- tag=tag1,tag2 filtra notas que tengan cualquier de esas etiquetas (OR); se puede combinar con q y order.

Ejemplos:

GET /api/notes?q=reunión&order=alpha
GET /api/notes?tag=work
GET /api/notes?tag=work,ideas&q=plan

## 12. Posibles Mejoras Futuras
- Búsqueda por texto completo en notas (FTS / PostgreSQL trigram)
- Agrupación o color para etiquetas
- Archivado de notas
- Exportación / importación de notas (management commands)
- Tests unitarios (pytest / Django test framework)

## 13. Estructura Simplificada
```
myinner/
  manage.py
  myinner_backend/
  users/
  notes/
  frontend/
```

## 14. Solución de Problemas
- CSRF 403: Asegúrate de enviar cookies (withCredentials) y que la cookie csrftoken exista.
- Archivos multimedia: subir imagen de perfil -> se sirven en /media/ en DEBUG.
- Sesión no persiste: Revisar ajustes de cookies del navegador (3rd-party blocking).

## 15. Perfil (Edición Avanzada)

Ahora puedes actualizar también username y email desde /api/profile/ (PUT/PATCH parcial). Validaciones:
- Username mínimo 3 caracteres y único (case-insensitive)
- Email único (case-insensitive), se normaliza a minúsculas
- Enviar `remove_image=1` en multipart/form-data para eliminar el avatar actual

Campos soportados (multipart): username, email, first_name, last_name, nickname, age, gender, profile_image, remove_image.

## 16. Licencia
Uso personal / educativo.

---
Hecho con Django + React.