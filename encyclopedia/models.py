from django.db import models


class EncyclopediaEntity(models.Model):
    wikidata_id = models.CharField(max_length=32, unique=True)
    label = models.CharField(max_length=300, blank=True)
    label_fr = models.CharField(max_length=300, blank=True)
    description_fr = models.TextField(blank=True)
    wikipedia_url_fr = models.URLField(blank=True)
    props = models.JSONField(default=dict, blank=True)
    image_url = models.URLField(blank=True)
    image_attribution = models.TextField(blank=True)
    license = models.CharField(max_length=200, blank=True)
    pageviews_60d = models.PositiveIntegerField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.label_fr or self.label or self.wikidata_id


class ImportJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        RUNNING = "running", "En cours"
        DONE = "done", "Terminé"
        FAILED = "failed", "Échec"

    collection = models.ForeignKey(
        "collection.Collection", on_delete=models.CASCADE, related_name="import_jobs"
    )
    params = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    progress = models.JSONField(default=dict, blank=True)
    errors = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Import {self.collection.slug} ({self.status})"
