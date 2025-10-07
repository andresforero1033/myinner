from django.db import models
from django.contrib.auth.models import AbstractUser
from encrypted_model_fields.fields import EncryptedEmailField, EncryptedCharField


class CustomUser(AbstractUser):
	GENDER_CHOICES = [
		('M', 'Masculino'),
		('F', 'Femenino'),
		('NB', 'No binario'),
		('O', 'Otro'),
		('P', 'Prefiero no decir'),
	]
	# Campos encriptados para proteger información sensible
	email = EncryptedEmailField(max_length=254, unique=True)
	first_name = EncryptedCharField(max_length=150, blank=True)
	last_name = EncryptedCharField(max_length=150, blank=True)
	
	# Campos no sensibles permanecen sin encriptar
	nickname = models.CharField(max_length=50, blank=True, null=True)
	age = models.PositiveIntegerField(blank=True, null=True)
	gender = models.CharField(max_length=2, choices=GENDER_CHOICES, blank=True, null=True)
	profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.username


class UserPreference(models.Model):
	THEME_CHOICES = [('light', 'Claro'), ('dark', 'Oscuro')]
	COLOR_CHOICES = [
		('#007bff', 'Azul'), ('#28a745', 'Verde'), ('#dc3545', 'Rojo'), ('#ffc107', 'Amarillo'),
		('#17a2b8', 'Cian'), ('#6f42c1', 'Morado'), ('#fd7e14', 'Naranja'), ('#e83e8c', 'Rosa'),
	]
	user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='preferences')
	theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
	primary_color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#007bff')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Preferencias de {self.user.username}"

# Create your models here.
