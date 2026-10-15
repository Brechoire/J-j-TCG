from django.contrib import admin

from .models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "display_order")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("status",)
