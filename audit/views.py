"""
Views para auditoría y análisis de logs
Proporciona endpoints para consultar y analizar logs de auditoría
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta, datetime

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar logs de auditoría
    Solo lectura, disponible para administradores
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['actor__username', 'object_repr', 'content_type__model']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']
    
    def _map_action_param(self, action_param: str):
        """Mapea el parámetro de acción (string) al valor entero esperado por LogEntry.action."""
        if action_param is None:
            return None
        value = action_param.strip().lower()
        mapping = {
            'create': LogEntry.Action.CREATE,
            'update': LogEntry.Action.UPDATE,
            'delete': LogEntry.Action.DELETE,
            'access': getattr(LogEntry.Action, 'ACCESS', None),
        }
        # Si es número como string devolver entero
        if value.isdigit():
            return int(value)
        return mapping.get(value)

    def get_queryset(self):
        """
        Filtra logs basado en parámetros de query
        """
        queryset = LogEntry.objects.select_related('actor', 'content_type').all()
        
        # Filtros por parámetros
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(actor_id=user_id)
        
        action = self._map_action_param(self.request.query_params.get('action', None))
        if action is not None:
            queryset = queryset.filter(action=action)
        
        model_name = self.request.query_params.get('model', None)
        if model_name:
            try:
                # Permitir 'app_label.Model' o solo 'model'
                if '.' in model_name:
                    app_label, model = model_name.split('.', 1)
                    content_type = ContentType.objects.get(app_label=app_label, model=model.lower())
                else:
                    content_type = ContentType.objects.get(model=model_name.lower())
                queryset = queryset.filter(content_type=content_type)
            except ContentType.DoesNotExist:
                pass
        
        # Filtro por rango de fechas
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=from_date)
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=to_date)
            except ValueError:
                pass
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Lista logs con información adicional
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serialized_data = []
            for log_entry in page:
                serialized_data.append({
                    'id': log_entry.id,
                    'timestamp': log_entry.timestamp,
                    'actor': log_entry.actor.username if log_entry.actor else 'System',
                    'action': log_entry.action,
                    'model': (f"{log_entry.content_type.app_label}.{log_entry.content_type.model}" if log_entry.content_type else 'Unknown'),
                    'object_id': log_entry.object_id,
                    'object_repr': log_entry.object_repr,
                    'changes': log_entry.changes,
                    'additional_data': log_entry.additional_data,
                    'remote_addr': log_entry.remote_addr,
                })
            
            return self.get_paginated_response(serialized_data)
        
        # Si no hay paginación, devolver todos los resultados
        serialized_data = []
        for log_entry in queryset:
            serialized_data.append({
                'id': log_entry.id,
                'timestamp': log_entry.timestamp,
                'actor': log_entry.actor.username if log_entry.actor else 'System',
                'action': log_entry.action,
                'model': (f"{log_entry.content_type.app_label}.{log_entry.content_type.model}" if log_entry.content_type else 'Unknown'),
                'object_id': log_entry.object_id,
                'object_repr': log_entry.object_repr,
                'changes': log_entry.changes,
                'additional_data': log_entry.additional_data,
                'remote_addr': log_entry.remote_addr,
            })
        
        return Response(serialized_data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estadísticas de auditoría
        """
        queryset = self.get_queryset()
        
        # Estadísticas básicas
        total_logs = queryset.count()
        
        # Logs por acción
        actions_stats = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Logs por modelo
        models_stats = queryset.select_related('content_type').values(
            'content_type__app_label', 'content_type__model'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Logs por usuario (top 10)
        users_stats = queryset.filter(actor__isnull=False).values(
            'actor__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Actividad por día (últimos 30 días)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_activity = queryset.filter(
            timestamp__gte=thirty_days_ago
        ).extra(
            select={'day': "date(timestamp)"}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        return Response({
            'total_logs': total_logs,
            'actions': list(actions_stats),
            'models': list(models_stats),
            'top_users': list(users_stats),
            'daily_activity': list(daily_activity),
            'period': {
                'from': thirty_days_ago.isoformat(),
                'to': timezone.now().isoformat()
            }
        })
    
    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """
        Actividad detallada de un usuario específico
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id parameter is required'}, status=400)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        
        # Logs del usuario
        user_logs = LogEntry.objects.filter(actor=user).order_by('-timestamp')
        
        # Estadísticas del usuario
        total_actions = user_logs.count()
        recent_actions = user_logs.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # Acciones por tipo
        actions_breakdown = user_logs.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Actividad reciente (últimas 20 acciones)
        recent_logs = []
        for log in user_logs[:20]:
            recent_logs.append({
                'timestamp': log.timestamp,
                'action': log.action,
                'model': (f"{log.content_type.app_label}.{log.content_type.model}" if log.content_type else 'Unknown'),
                'object_repr': log.object_repr,
                'changes_count': len(log.changes) if log.changes else 0
            })
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': str(user.email) if hasattr(user, 'email') else None,
            },
            'statistics': {
                'total_actions': total_actions,
                'recent_actions_7d': recent_actions,
                'actions_breakdown': list(actions_breakdown)
            },
            'recent_activity': recent_logs
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def audit_dashboard_data(request):
    """
    Datos para el dashboard de auditoría
    """
    # Período de análisis
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    queryset = LogEntry.objects.filter(timestamp__gte=start_date)
    
    # Métricas principales
    total_actions = queryset.count()
    unique_users = queryset.filter(actor__isnull=False).values('actor').distinct().count()
    
    # Acciones críticas (crear, modificar, eliminar)
    critical_actions = queryset.filter(
        action__in=[LogEntry.Action.CREATE, LogEntry.Action.UPDATE, LogEntry.Action.DELETE]
    ).count()
    
    # Detecciones de seguridad (logins fallidos, etc.)
    # Esto requeriría logs adicionales, por ahora simulamos
    security_events = 0
    
    # Actividad por hora del día
    hourly_activity = []
    for hour in range(24):
        count = queryset.filter(timestamp__hour=hour).count()
        hourly_activity.append({'hour': hour, 'count': count})
    
    # Modelos más modificados
    top_models = queryset.select_related('content_type').values(
        'content_type__app_label', 'content_type__model'
    ).annotate(count=Count('id')).order_by('-count')[:5]
    
    # Usuarios más activos
    top_users = queryset.filter(actor__isnull=False).values(
        'actor__username'
    ).annotate(count=Count('id')).order_by('-count')[:5]
    
    return Response({
        'period': {
            'days': days,
            'start_date': start_date.isoformat(),
            'end_date': timezone.now().isoformat()
        },
        'metrics': {
            'total_actions': total_actions,
            'unique_users': unique_users,
            'critical_actions': critical_actions,
            'security_events': security_events
        },
        'charts': {
            'hourly_activity': hourly_activity,
            'top_models': list(top_models),
            'top_users': list(top_users)
        }
    })


@staff_member_required
def audit_dashboard_view(request):
    """
    Vista HTML para el dashboard de auditoría
    """
    context = {
        'title': 'Dashboard de Auditoría',
        'recent_logs_count': LogEntry.objects.count()
    }
    return render(request, 'audit/dashboard.html', context)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def cleanup_old_logs(request):
    """
    Limpieza de logs antiguos basada en políticas de retención
    """
    from django.conf import settings
    
    retain_days = getattr(settings, 'AUDIT_SETTINGS', {}).get('RETAIN_LOGS_DAYS', 365)
    cutoff_date = timezone.now() - timedelta(days=retain_days)
    
    # Contar logs que se eliminarán
    old_logs = LogEntry.objects.filter(timestamp__lt=cutoff_date)
    count_to_delete = old_logs.count()
    
    if request.data.get('confirm', False):
        # Realizar la eliminación
        deleted_count = old_logs.delete()[0]
        
        return Response({
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat(),
            'retain_days': retain_days
        })
    else:
        # Solo mostrar cuántos se eliminarían
        return Response({
            'preview': True,
            'logs_to_delete': count_to_delete,
            'cutoff_date': cutoff_date.isoformat(),
            'retain_days': retain_days,
            'message': 'Use confirm=true to actually delete the logs'
        })