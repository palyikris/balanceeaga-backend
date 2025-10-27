from django.contrib import admin
from .models import FileImport


@admin.register(FileImport)
class FIAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "original_name", "status", "created_at")
    search_fields = ("original_name", "user_id", "checksum_sha256")
    list_filter = ("status", "source_hint", "adapter_hint")
