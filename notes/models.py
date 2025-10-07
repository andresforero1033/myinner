from django.db import models
from django.conf import settings
from encrypted_model_fields.fields import EncryptedTextField


class Tag(models.Model):
	name = models.CharField(max_length=40, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class Note(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes')
	title = models.CharField(max_length=200)
	# Contenido encriptado para proteger datos sensibles
	content = EncryptedTextField()
	tags = models.ManyToManyField(Tag, related_name='notes', blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.title} - {self.user.username}"

# Create your models here.
