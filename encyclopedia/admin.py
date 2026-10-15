from django.contrib import admin

from .models import EncyclopediaEntity, ImportJob


@admin.register(EncyclopediaEntity)
class EncyclopediaEntityAdmin(admin.ModelAdmin):
    list_display = ("wikidata_id", "label_fr", "pageviews_60d", "synced_at")
    search_fields = ("wikidata_id", "label_fr")


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ("collection", "status", "started_at", "finished_at")
    list_filter = ("status",)
