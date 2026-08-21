from django.contrib import admin
from .models import Martyr, SyncRun

@admin.register(Martyr)
class MartyrAdmin(admin.ModelAdmin):
    list_display = ("name", "hometown", "zone", "grave_row", "grave_number", "last_seen_at")
    search_fields = ("name", "normalized_name", "hometown")
    list_filter = ("zone", "is_verified")
    readonly_fields = ("source_id", "source_url", "source_hash", "first_seen_at", "last_seen_at")

admin.site.register(SyncRun)

