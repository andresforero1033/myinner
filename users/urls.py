from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    PreferenceView, NoteListCreateView, NoteRetrieveUpdateDestroyView,
    CSRFTokenView, HealthCheckView, MeView, APIRootView, TagAutocompleteView
)

urlpatterns = [
    path('', APIRootView.as_view(), name='api-root'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/csrf/', CSRFTokenView.as_view(), name='csrf'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('health/', HealthCheckView.as_view(), name='health'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('preferences/', PreferenceView.as_view(), name='preferences'),
    path('notes/', NoteListCreateView.as_view(), name='notes-list-create'),
    path('notes/<int:pk>/', NoteRetrieveUpdateDestroyView.as_view(), name='note-detail'),
    path('tags/', TagAutocompleteView.as_view(), name='tags-autocomplete'),
]