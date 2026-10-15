import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)


class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    last_free_opened_at = models.DateTimeField(null=True, blank=True)
    total_opened = models.PositiveIntegerField(default=0)
    unique_discovered = models.PositiveIntegerField(default=0)
    preferences = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Profil de {self.user.username}"
