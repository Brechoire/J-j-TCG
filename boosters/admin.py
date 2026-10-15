from django.contrib import admin

from .models import BoosterOpening, BoosterOpeningCard


class BoosterOpeningCardInline(admin.TabularInline):
    model = BoosterOpeningCard
    extra = 0


@admin.register(BoosterOpening)
class BoosterOpeningAdmin(admin.ModelAdmin):
    list_display = ("player", "collection", "kind", "created_at")
    list_filter = ("kind", "collection")
    inlines = [BoosterOpeningCardInline]
