from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.middleware.csrf import get_token
from rest_framework import generics, permissions, views
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q

from .models import CustomUser, UserPreference
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UserPreferenceSerializer, NoteSerializer
)
from notes.models import Note


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        # Asegurar preferencias
        UserPreference.objects.get_or_create(user=user)
        return Response(UserSerializer(user, context={'request': request}).data)

    def get(self, request):
        """Simple ping para obtener cookie CSRF y saber si ya está autenticado."""
        # Forzar generación de token CSRF (set-cookie en respuesta si procede)
        get_token(request)
        if request.user.is_authenticated:
            UserPreference.objects.get_or_create(user=request.user)
            return Response({'authenticated': True, 'user': UserSerializer(request.user, context={'request': request}).data})
        return Response({'authenticated': False})


class CSRFTokenView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        get_token(request)
        return Response({'detail': 'CSRF cookie establecida'})


class HealthCheckView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'status': 'ok'})


class MeView(views.APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'No autenticado'}, status=401)
        UserPreference.objects.get_or_create(user=request.user)
        return Response(UserSerializer(request.user, context={'request': request}).data)


class APIRootView(views.APIView):
    """Listado simple de endpoints disponibles para evitar 404 en /api/."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        base = request.build_absolute_uri('.')  # termina en /api/
        return Response({
            'auth_register': base + 'auth/register/',
            'auth_login': base + 'auth/login/',
            'auth_logout': base + 'auth/logout/',
            'auth_me': base + 'auth/me/',
            'csrf': base + 'auth/csrf/',
            'health': base + 'health/',
            'profile': base + 'profile/',
            'preferences': base + 'preferences/',
            'notes': base + 'notes/'
        })


class LogoutView(views.APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'Sesión cerrada'})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        # permitir PUT parcial sin exigir todos los campos
        kwargs['partial'] = True
        return self.partial_update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.partial_update(request, *args, **kwargs)


class PreferenceView(views.APIView):
    def get(self, request):
        prefs, _ = UserPreference.objects.get_or_create(user=request.user)
        return Response(UserPreferenceSerializer(prefs).data)

    def put(self, request):
        prefs, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class NoteListCreateView(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Note.objects.none()
        qs = Note.objects.filter(user=self.request.user)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
        tag_param = self.request.query_params.get('tag')
        if tag_param:
            tags = [t.strip().lower() for t in tag_param.split(',') if t.strip()]
            if tags:
                qs = qs.filter(tags__name__in=tags).distinct()
        order = self.request.query_params.get('order')
        if order == 'alpha':
            qs = qs.order_by('title')
        elif order == 'oldest':
            qs = qs.order_by('created_at')
        else:
            qs = qs.order_by('-created_at')
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoteRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Note.objects.none()
        return Note.objects.filter(user=self.request.user)
