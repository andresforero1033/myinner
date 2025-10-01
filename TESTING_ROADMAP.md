# Testing Roadmap - Myinner

Este documento describe las pruebas preparadas para futuras implementaciones.

## Estado actual
✅ **11 tests activos** - Autenticación, CRUD notas, permisos, tags  
✅ **11 tests preparados** - Estructuras listas para paginación y verificación email

## 📄 Paginación (PaginationTests)

### Backend requerido:
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

# users/views.py - NoteListCreateView
class NoteListCreateView(generics.ListCreateAPIView):
    pagination_class = PageNumberPagination  # Añadir esta línea
```

### Frontend requerido:
```jsx
// Componente Pagination.jsx
const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  // Botones Previous/Next con números de página
}

// Dashboard.jsx - manejar respuesta paginada
const { count, next, previous, results } = response.data;
```

### Tests preparados:
- `test_paginated_response_structure` - Validar estructura {count, next, previous, results}
- `test_page_size_limit` - Verificar límite de 10 items por página
- `test_navigation_links` - Links next/previous correctos
- `test_pagination_with_search_and_filters` - Paginación + filtros
- `test_invalid_page_numbers` - Edge cases (page=0, page=abc, etc.)

## ✉️ Verificación Email (EmailVerificationTests) 

### Backend requerido:
```python
# models.py
class EmailVerificationToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

# CustomUser - añadir campo
is_email_verified = models.BooleanField(default=False)

# urls.py - nuevos endpoints
path('verify-email/', VerifyEmailView.as_view()),
path('resend-verification/', ResendVerificationView.as_view()),
```

### Email backend:
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # o SendGrid
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

### Frontend requerido:
```jsx
// VerificationPage.jsx - página para /verify/:token
// ProfileBadge.jsx - mostrar estado verificado/no verificado
// ResendButton.jsx - botón "Reenviar email de verificación"
```

### Tests preparados:
- `test_registration_sends_verification_email` - Email enviado tras registro
- `test_valid_token_verifies_email` - Token válido actualiza estado
- `test_invalid_or_expired_token` - Manejo de errores
- `test_resend_verification_email` - Reenvío con rate limiting
- `test_already_verified_user_cannot_reverify` - Prevenir re-verificación
- `test_verification_status_in_profile` - Campo en /auth/me/

## 🚀 Pasos para activar tests

### 1. Paginación
```bash
# Implementar backend (settings + view)
# Implementar frontend (componente Pagination)
# Quitar skipTest de PaginationTests
python manage.py test notes.tests.PaginationTests
```

### 2. Verificación Email  
```bash
# Crear modelo EmailVerificationToken + migración
# Implementar VerifyEmailView + ResendVerificationView
# Configurar email backend
# Quitar skipTest de EmailVerificationTests
python manage.py test users.tests.EmailVerificationTests
```

## 📋 Checklist implementación

### Paginación
- [ ] Configurar `PAGE_SIZE` en settings
- [ ] Añadir `pagination_class` en NoteListCreateView
- [ ] Crear componente `Pagination.jsx`
- [ ] Actualizar `Dashboard.jsx` para manejar respuesta paginada
- [ ] Activar tests: remover `self.skipTest()` en `PaginationTests`

### Verificación Email
- [ ] Crear modelo `EmailVerificationToken`
- [ ] Añadir campo `is_email_verified` a `CustomUser`
- [ ] Implementar `VerifyEmailView` y `ResendVerificationView`
- [ ] Configurar backend de email (SMTP/SendGrid)
- [ ] Crear utility para generar/validar tokens
- [ ] Actualizar `UserSerializer` para incluir `is_email_verified`
- [ ] Crear frontend para verificación
- [ ] Activar tests: remover `self.skipTest()` en `EmailVerificationTests`

## 🎯 Priorización sugerida

1. **Paginación** (impacto inmediato UX, implementación simple)
2. **Verificación Email** (seguridad fundamental, implementación media)

## ⚠️ Consideraciones

- **Rate limiting**: Implementar en resend (máx 3/hora)
- **Token security**: Usar `secrets.token_urlsafe(32)` 
- **Email templates**: HTML bonito con logo y styling
- **Cleanup job**: Tokens expirados >24h (management command)
- **Testing**: Usar `django.core.mail.outbox` para capturar emails en tests