from django.contrib import admin
from .models import Note, Tag


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
	list_display = ('title', 'user', 'tag_list', 'created_at', 'updated_at')
	search_fields = ('title', 'content', 'user__username')
	list_filter = ('created_at', 'tags')

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.prefetch_related('tags')

	def tag_list(self, obj):
		return ", ".join(t.name for t in obj.tags.all())
	tag_list.short_description = 'Tags'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	search_fields = ('name', )
	list_display = ('name', 'created_at')

# Register your models here.
