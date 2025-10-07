# PostgreSQL con SSL - Guía de Deployment

## 🚀 **CONFIGURACIÓN POSTGRESQL CON SSL IMPLEMENTADA**

### 🔧 **Cambios Realizados**

La aplicación ahora soporta configuración dual:
- **Desarrollo**: SQLite (como antes)
- **Producción**: PostgreSQL con SSL obligatorio

### 📋 **Archivos Modificados**

1. **`myinner_backend/settings.py`** - Configuración dual DATABASE
2. **`.env.example`** - Variables de entorno para producción  
3. **`requirements-production.txt`** - Dependencias adicionales
4. **`logs/`** - Directorio para logging en producción

---

## 🔐 **CONFIGURACIÓN DE SEGURIDAD POSTGRESQL**

### **1. Variables de Entorno (.env)**

Crear archivo `.env` en raíz del proyecto:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=tu-clave-secreta-super-larga-y-segura-cambiar-en-produccion
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com

# PostgreSQL Database
DATABASE_URL=postgresql://usuario:password@localhost:5432/myinner_db
DB_NAME=myinner_db
DB_USER=myinner_user
DB_PASSWORD=tu-password-super-seguro
DB_HOST=localhost
DB_PORT=5432
DB_SSL_MODE=require

# Security
CORS_ALLOWED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
```

### **2. Configuración PostgreSQL**

La aplicación se configura automáticamente según el ambiente:

```python
# DESARROLLO (DEBUG=True)
- Usa SQLite como antes
- Cookies HTTP (no HTTPS)
- CORS para localhost:3000-3002

# PRODUCCIÓN (DEBUG=False)  
- PostgreSQL con SSL requerido
- Cookies HTTPS solamente
- CORS desde variables de entorno
- Logging a archivos
- Headers de seguridad HTTPS
```

---

## 🐘 **INSTALACIÓN POSTGRESQL EN SERVIDOR**

### **Ubuntu/Debian**

```bash
# 1. Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# 2. Configurar usuario y base de datos
sudo -u postgres psql
CREATE DATABASE myinner_db;
CREATE USER myinner_user WITH ENCRYPTED PASSWORD 'tu-password-seguro';
GRANT ALL PRIVILEGES ON DATABASE myinner_db TO myinner_user;
ALTER USER myinner_user CREATEDB;
\q

# 3. Configurar SSL en PostgreSQL
sudo nano /etc/postgresql/14/main/postgresql.conf
# Descomentar y modificar:
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'

# 4. Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

### **Verificar SSL está activo**

```bash
sudo -u postgres psql -c "SHOW ssl;"
# Debe mostrar: ssl | on
```

---

## 🚀 **DEPLOYMENT EN PRODUCCIÓN**

### **1. Preparar Servidor**

```bash
# Instalar dependencias del sistema
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql

# Clonar repositorio
git clone https://github.com/andresforero1033/myinner.git
cd myinner

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-production.txt
```

### **2. Configurar Variables de Entorno**

```bash
# Crear archivo .env con valores reales
cp .env.example .env
nano .env

# Configurar con datos reales:
DEBUG=False
SECRET_KEY=generar-clave-super-segura-64-caracteres-minimo
DATABASE_URL=postgresql://myinner_user:password@localhost:5432/myinner_db
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
```

### **3. Migrar Base de Datos**

```bash
# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic
```

### **4. Verificar Configuración**

```bash
# Check de sistema
python manage.py check --deploy

# Probar conexión PostgreSQL
python manage.py dbshell
\conninfo
# Debe mostrar SSL connection
\q
```

---

## 🔒 **CARACTERÍSTICAS DE SEGURIDAD ACTIVADAS**

### **🛡️ Database Security**
- ✅ **PostgreSQL con SSL obligatorio** (sslmode=require)
- ✅ **Connection pooling** (CONN_MAX_AGE=600)
- ✅ **Health checks** automáticos
- ✅ **Timeout configurado** (30s connect_timeout)
- ✅ **Isolation level** serializable por defecto

### **🍪 Cookie Security**
- ✅ **HTTPS obligatorio** en producción (Secure=True)
- ✅ **SameSite=Strict** para CSRF/Session
- ✅ **HttpOnly** activado para seguridad XSS
- ✅ **Nombres explícitos** de cookies

### **🌐 HTTPS Security Headers**
- ✅ **HSTS** activado (1 año + subdomains)  
- ✅ **XSS Filter** del navegador
- ✅ **Content Type Nosniff**
- ✅ **X-Frame-Options: DENY**
- ✅ **SSL Redirect** obligatorio
- ✅ **Referrer Policy** restrictiva

### **📊 Logging & Monitoring**
- ✅ **Logs estructurados** con timestamps
- ✅ **Niveles configurables** por ambiente
- ✅ **Security events** logging
- ✅ **Archivos rotativos** en producción

---

## 🧪 **TESTING DE CONFIGURACIÓN**

### **Test Local con PostgreSQL**

```bash
# 1. Instalar PostgreSQL localmente
# 2. Crear .env con PostgreSQL config
echo "USE_POSTGRESQL=True" >> .env
echo "DB_NAME=myinner_test" >> .env

# 3. Ejecutar tests
python manage.py test
```

### **Test de SSL Connection**

```python
# Script de verificación
import psycopg2
import ssl

conn = psycopg2.connect(
    host="localhost",
    database="myinner_db", 
    user="myinner_user",
    password="password",
    sslmode="require"
)

cursor = conn.cursor()
cursor.execute("SELECT version();")
print("PostgreSQL version:", cursor.fetchone())

# Verificar SSL
cursor.execute("SHOW ssl;")
print("SSL status:", cursor.fetchone())

conn.close()
```

---

## 📈 **MONITOREO Y MANTENIMIENTO**

### **Logs Importantes**

```bash
# Logs de Django
tail -f logs/django.log

# Logs de PostgreSQL  
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Logs de Nginx (si usas)
sudo tail -f /var/log/nginx/access.log
```

### **Comandos de Mantenimiento**

```bash
# Backup de base de datos
pg_dump -h localhost -U myinner_user myinner_db > backup.sql

# Restore de base de datos
psql -h localhost -U myinner_user myinner_db < backup.sql

# Verificar conexiones activas
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Verificar tamaño de base de datos
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('myinner_db'));"
```

---

## ⚡ **PERFORMANCE OPTIMIZATIONS**

### **PostgreSQL Tuning**

```sql
-- Configuraciones recomendadas en postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB  
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### **Django Database Optimizations**

```python
# En settings.py ya configurado:
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,           # Connection pooling
        'CONN_HEALTH_CHECKS': True,   # Health checks
        'OPTIONS': {
            'sslmode': 'require',      # SSL obligatorio
            'connect_timeout': 30,     # Timeout
        }
    }
}
```

---

## 🚨 **TROUBLESHOOTING**

### **Problemas Comunes**

1. **Error SSL connection**
   ```bash
   # Verificar que PostgreSQL tiene SSL activo
   sudo -u postgres psql -c "SHOW ssl;"
   ```

2. **Permission denied for database**
   ```bash
   # Dar permisos al usuario
   sudo -u postgres psql
   GRANT ALL PRIVILEGES ON DATABASE myinner_db TO myinner_user;
   ```

3. **CORS errors en producción**
   ```bash
   # Verificar variables de entorno
   echo $CORS_ALLOWED_ORIGINS
   ```

4. **Static files no cargan**
   ```bash
   # Ejecutar collectstatic
   python manage.py collectstatic --noinput
   ```

---

## ✅ **CHECKLIST DE DEPLOYMENT**

- [ ] PostgreSQL instalado y configurado con SSL
- [ ] Usuario y base de datos creados
- [ ] Archivo `.env` configurado con valores reales
- [ ] Dependencias de producción instaladas
- [ ] Migraciones ejecutadas
- [ ] Static files recopilados
- [ ] `python manage.py check --deploy` pasa
- [ ] SSL connection verificada
- [ ] Logs funcionando correctamente
- [ ] Backup strategy configurada

---

**🎯 RESULTADO: Base de datos PostgreSQL con SSL completamente configurada y lista para producción con máxima seguridad.**