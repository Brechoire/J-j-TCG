from django.db import models


class Collection(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archivée"

    #: Libellé de type de carte par config wiki (repli si `card_type` absent).
    CARD_TYPE_LABELS = {
        ("Q5", "Q937857"): "Footballeur",
        ("Q5", "Q628099"): "Entraîneur",
        ("Q483110", None): "Stade",
    }

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    display_order = models.PositiveIntegerField(default=0)
    import_config = models.JSONField(default=dict, blank=True)
    gameplay_params = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def card_type_label(self) -> str:
        """Type affiché sur le badge des cartes (Footballeur, Entraîneur, Stade…).

        Priorité à `import_config["card_type"]`, sinon déduit de la config wiki.
        """
        config = self.import_config or {}
        if config.get("card_type"):
            return config["card_type"]
        return self.CARD_TYPE_LABELS.get(
            (config.get("instance_of"), config.get("occupation_qid")), "Foot"
        )


class Pack(models.Model):
    """Sous-périmètre tirage au sein d'une collection (ex. Français, OM, Ligue 1 2001-2002).

    Appartenance mixte : règles sur les props d'entité (`filter_params`,
    évaluées à la lecture — les nouveaux imports rejoignent seuls) + membres
    explicites curés (`cards`, indispensable pour les saisons historiques).
    Une carte appartient à plusieurs packs ; la fiche carte les affiche.
    """

    class Kind(models.TextChoices):
        NATIONALITY = "nationality", "Nationalité"
        CLUB = "club", "Club"
        SEASON = "season", "Saison / compétition"
        CUSTOM = "custom", "Personnalisé"

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="packs")
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.CUSTOM)
    description = models.TextField(blank=True)
    #: Règles sur les props d'entité, ex. {"nationality": "France"}
    #: ou {"club": "Olympique de Marseille"}. Comparaison normalisée
    #: (minuscules, sans accents) via `cards.country_flags.normalize`.
    filter_params = models.JSONField(default=dict, blank=True)
    #: Membres curés à la main (saisons historiques, sélections).
    cards = models.ManyToManyField("cards.Card", blank=True, related_name="packs")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "slug"], name="unique_pack_collection_slug"
            )
        ]

    def __str__(self) -> str:
        return f"{self.collection.slug} / {self.name}"
