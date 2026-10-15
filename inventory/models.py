from django.db import models


class InventoryEntry(models.Model):
    player = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="inventory_entries"
    )
    card = models.ForeignKey(
        "cards.Card", on_delete=models.PROTECT, related_name="inventory_entries"
    )
    quantity = models.PositiveIntegerField(default=1)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_obtained_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["player", "card"], name="unique_inventory_player_card")
        ]
        indexes = [models.Index(fields=["player", "card"])]

    def __str__(self) -> str:
        return f"{self.player} x{self.quantity} {self.card}"
