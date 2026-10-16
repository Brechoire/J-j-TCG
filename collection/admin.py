from django.contrib import admin

from .models import Collection, Pack


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "display_order")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("status",)

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if field and db_field.name == "import_config":
            field.help_text = (
                "Type wiki (JSON) : joueur "
                '{"instance_of": "Q5", "occupation_qid": "Q937857", '
                '"card_type": "Footballeur"} ; entraîneur '
                '{"instance_of": "Q5", "occupation_qid": "Q628099", '
                '"card_type": "Entraîneur"} ; stade de foot '
                '{"instance_of": "Q483110", "occupation_qid": null, '
                '"sport_qid": "Q2736", "card_type": "Stade"}. '
                "Vide = défauts foot."
            )
        return field


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ("name", "collection", "kind", "is_active", "display_order")
    list_filter = ("collection", "kind", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("cards",)
    ordering = ("collection", "display_order", "name")

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if field and db_field.name == "filter_params":
            field.help_text = (
                "Règles sur les props (JSON), ex. "
                '{"nationality": "France"} ou '
                '{"club": "Olympique de Marseille"}. '
                "Comparaison insensible casse/accents. "
                "Vide = curation manuelle seule."
            )
        return field
