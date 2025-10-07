# Implementación de Encriptación a Nivel de Campo - MyInner

## Descripción General

Este documento describe la implementación de encriptación a nivel de campo para proteger datos sensibles en la aplicación MyInner. La encriptación se aplica de forma transparente utilizando `django-encrypted-model-fields`.

## Campos Encriptados

### Modelo Note (`notes/models.py`)
- **content**: `EncryptedTextField` - El contenido completo de las notas se encripta para proteger información personal y sensible.

### Modelo CustomUser (`users/models.py`)
- **email**: `EncryptedEmailField` - Direcciones de correo electrónico encriptadas
- **first_name**: `EncryptedCharField` - Nombres encriptados
- **last_name**: `EncryptedCharField` - Apellidos encriptados

### Campos No Encriptados
Los siguientes campos permanecen sin encriptar por razones de funcionalidad:
- `username` - Necesario para autenticación y búsquedas
- `nickname` - Información no sensible, usada para visualización
- `age`, `gender` - Datos demográficos no identificables
- `created_at`, `updated_at` - Metadatos del sistema

## Configuración Técnica

### Dependencias
```bash
pip install django-encrypted-model-fields cryptography
```

### Variables de Entorno
```env
# Clave de encriptación (32 bytes en base64)
FIELD_ENCRYPTION_KEY=yiAdYdW3LskGqOVfe6Hn0EMBINNPeXfbh1x6Yv8rTVY=
```

### Configuración en settings.py
```python
# Validación de clave de encriptación
FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY')
if len(FIELD_ENCRYPTION_KEY.encode()) != 44:  # 32 bytes en base64 = 44 caracteres
    import warnings
    warnings.warn(
        "FIELD_ENCRYPTION_KEY debe tener exactamente 32 bytes. "
        "Usa: from cryptography.fernet import Fernet; print(Fernet.generate_key())"
    )
```

## Generación de Claves

Utiliza el script proporcionado para generar claves seguras:

```python
# generate_encryption_key.py
from cryptography.fernet import Fernet
import warnings

key = Fernet.generate_key()
print(f"Clave de encriptación generada: {key.decode()}")

warnings.warn(
    "⚠️  IMPORTANTE: Guarda esta clave de forma segura. "
    "Si la pierdes, no podrás acceder a los datos encriptados."
)
```

## Comportamiento de la Encriptación

### Transparencia
- **Escritura**: Los datos se encriptan automáticamente al guardar
- **Lectura**: Los datos se desencriptan automáticamente al consultar
- **Búsquedas**: Las búsquedas en campos encriptados son limitadas (solo igualdad exacta)

### Ejemplo de Uso
```python
# Crear usuario con datos encriptados
user = CustomUser.objects.create_user(
    username='usuario123',
    email='usuario@ejemplo.com',  # Se encripta automáticamente
    first_name='Juan',            # Se encripta automáticamente
    last_name='Pérez'             # Se encripta automáticamente
)

# Acceder a datos (se desencriptan automáticamente)
print(user.email)       # 'usuario@ejemplo.com'
print(user.first_name)  # 'Juan'
```

### Limitaciones de Búsqueda
```python
# ✅ Búsquedas permitidas
User.objects.filter(email='usuario@ejemplo.com')  # Igualdad exacta

# ❌ Búsquedas NO permitidas en campos encriptados
User.objects.filter(email__icontains='usuario')   # Contiene
User.objects.filter(first_name__startswith='J')   # Empieza con
```

## Seguridad y Consideraciones

### Fortalezas
- **Encriptación AES-256**: Algoritmo robusto y ampliamente aceptado
- **Transparencia**: Sin cambios en la lógica de aplicación
- **Protección en reposo**: Datos seguros en la base de datos
- **Protección contra dump**: Respaldos de BD no exponen datos sensibles

### Consideraciones Importantes
- **Gestión de claves**: La clave debe mantenerse segura y backed up
- **Rendimiento**: Ligero overhead en operaciones de BD
- **Búsquedas limitadas**: Solo igualdad exacta en campos encriptados
- **Migración**: Datos existentes se encriptan durante la migración

## Migraciones Aplicadas

### notes.0004_alter_note_content
- Convierte el campo `content` de `TextField` a `EncryptedTextField`
- Mantiene datos existentes (se encriptan automáticamente)

### users.0002_alter_customuser_email_alter_customuser_first_name_and_more
- Convierte `email` de `EmailField` a `EncryptedEmailField`
- Convierte `first_name` y `last_name` de `CharField` a `EncryptedCharField`
- Preserva la funcionalidad de validación de email

## Respaldo y Recuperación

### Respaldo de Claves
```bash
# Respaldar clave de encriptación (CRÍTICO)
echo $FIELD_ENCRYPTION_KEY > encryption_key_backup.txt
```

### Rotación de Claves
Para rotar claves (proceso avanzado):
1. Generar nueva clave con `generate_encryption_key.py`
2. Desencriptar todos los datos con clave antigua
3. Actualizar `FIELD_ENCRYPTION_KEY` con nueva clave
4. Re-encriptar todos los datos

## Pruebas de Funcionalidad

### Verificar Encriptación
```python
# Verificar que los datos se almacenan encriptados
from django.db import connection
from users.models import CustomUser

user = CustomUser.objects.create_user(
    username='test', 
    email='test@example.com',
    first_name='Test'
)

# Consulta directa a la BD debe mostrar datos encriptados
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT email, first_name FROM users_customuser WHERE username = %s", 
        ['test']
    )
    row = cursor.fetchone()
    print(f"Email encriptado en BD: {row[0]}")
    print(f"Nombre encriptado en BD: {row[1]}")

# Acceso vía ORM debe mostrar datos desencriptados
print(f"Email desencriptado: {user.email}")
print(f"Nombre desencriptado: {user.first_name}")
```

## Estado de Implementación

✅ **Completado:**
- Instalación de dependencias de encriptación
- Configuración de clave de encriptación
- Modificación de modelos Note y CustomUser
- Creación y aplicación de migraciones
- Validación de configuración

⏳ **Pendiente:**
- Pruebas unitarias para encriptación/desencriptación
- Documentación de procedimientos de respaldo
- Monitoreo de rendimiento con campos encriptados

## Soporte y Mantenimiento

Para preguntas o problemas relacionados con la encriptación de campos:
1. Verificar que `FIELD_ENCRYPTION_KEY` esté configurada correctamente
2. Confirmar que las dependencias estén instaladas
3. Revisar logs para errores de encriptación/desencriptación
4. Consultar documentación de `django-encrypted-model-fields`

---
*Implementación completada el: $(date)*
*Versión: 1.0*