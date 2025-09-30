from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserPreference


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
	fieldsets = UserAdmin.fieldsets + (
		('Perfil', {'fields': ('nickname', 'age', 'gender', 'profile_image')}),
	)
	list_display = ('username', 'email', 'nickname', 'age', 'gender', 'is_active')
	search_fields = ('username', 'email', 'nickname')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
	list_display = ('user', 'theme', 'primary_color')
	list_filter = ('theme', 'primary_color')

# Register your models here.
