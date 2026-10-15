import uuid

from django.db import models


class BoosterOpening(models.Model):
    class Kind(models.TextChoices):
        FREE = "free", "Gratuit"
        PAID = "paid", "Acheté"

    player = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="booster_openings"
    )
    collection = models.ForeignKey(
        "collection.Collection",
        on_delete=models.PROTECT,
        related_name="booster_openings",
    )
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.FREE)
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.UUIDField(unique=True, default=uuid.uuid4)
    result_cache = models.JSONField(default=dict, blank=True)
    cards = models.ManyToManyField(
        "cards.Card", through="BoosterOpeningCard", related_name="openings"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["player", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.player} {self.kind} {self.collection.slug} {self.created_at}"


class BoosterOpeningCard(models.Model):
    opening = models.ForeignKey(
        BoosterOpening, on_delete=models.CASCADE, related_name="opening_cards"
    )
    card = models.ForeignKey("cards.Card", on_delete=models.PROTECT, related_name="opening_cards")
    position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["opening", "card"], name="unique_opening_card"),
            models.UniqueConstraint(fields=["opening", "position"], name="unique_opening_position"),
        ]
