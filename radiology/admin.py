from django.contrib import admin
from .models import ProcessedDocument

@admin.register(ProcessedDocument)
class ProcessedDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'original_filename', 'processing_type', 'status', 'created_at')
    list_filter = ('processing_type', 'status', 'user')
    search_fields = ('original_filename', 'user__email')
    readonly_fields = ('created_at', 'updated_at')