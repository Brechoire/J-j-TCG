from django.contrib import admin

from .models import InventoryEntry


@admin.register(InventoryEntry)
class InventoryEntryAdmin(admin.ModelAdmin):
    list_display = ("player", "card", "quantity", "last_obtained_at")
