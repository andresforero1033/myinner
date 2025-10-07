"""
URLs para el módulo de auditoría
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'audit'

# Router para API REST
router = DefaultRouter()
router.register(r'logs', views.AuditLogViewSet, basename='auditlog')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/dashboard/', views.audit_dashboard_data, name='dashboard-data'),
    path('api/cleanup/', views.cleanup_old_logs, name='cleanup-logs'),
    
    # Vistas HTML
    path('dashboard/', views.audit_dashboard_view, name='dashboard'),
]