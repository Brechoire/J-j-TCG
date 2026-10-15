from django.contrib import admin

from .models import Card, Rarity
from .services import RarityAssignmentService


@admin.register(Rarity)
class RarityAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "draw_weight", "sale_value", "order", "is_active")
    ordering = ("order",)


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        "collection",
        "entity",
        "auto_score",
        "auto_rarity",
        "rarity",
        "is_locked",
        "is_active",
    )
    list_filter = ("collection", "rarity", "is_locked", "is_active")
    actions = ("recalculate_rarity",)

    @admin.action(description="Recalculer raretés auto (respecte verrous)")
    def recalculate_rarity(self, request, queryset):
        collections = {c.collection_id for c in queryset}
        from collection.models import Collection

        for col_id in collections:
            RarityAssignmentService().assign_collection(Collection.objects.get(pk=col_id))
