from django.db import models


class Collection(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archivée"

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
