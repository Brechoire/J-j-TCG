from django.db import models


class Rarity(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=16, default="#9ca3af")
    draw_weight = models.PositiveIntegerField(default=0)
    sale_value = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.name


class Card(models.Model):
    collection = models.ForeignKey(
        "collection.Collection", on_delete=models.PROTECT, related_name="cards"
    )
    entity = models.ForeignKey(
        "encyclopedia.EncyclopediaEntity",
        on_delete=models.PROTECT,
        related_name="cards",
    )
    rarity = models.ForeignKey(
        Rarity,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="final_cards",
    )
    auto_score = models.FloatField(null=True, blank=True)
    auto_rarity = models.ForeignKey(
        Rarity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="auto_cards",
    )
    is_manual_override = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sale_value_override = models.PositiveIntegerField(null=True, blank=True)
    game_meta = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "entity"], name="unique_card_collection_entity"
            )
        ]
        indexes = [
            models.Index(fields=["collection", "rarity", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.collection.slug} / {self.entity}"

    @property
    def effective_sale_value(self) -> int:
        if self.sale_value_override is not None:
            return self.sale_value_override
        if self.rarity_id and self.rarity.sale_value:
            return self.rarity.sale_value
        return 0
