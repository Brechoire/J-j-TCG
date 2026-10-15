"""Import Football incrémental, reprise, dry-run, réimport QID."""

from django.db import transaction
from django.utils import timezone


def run_football_import(
    collection_slug="football", limit=100, dry_run=False, qid=None, client=None
):
    from cards.models import Card
    from collection.models import Collection
    from encyclopedia.models import EncyclopediaEntity, ImportJob

    if client is None:
        from encyclopedia.wikidata import WikidataClient

        client = WikidataClient()

    collection = None
    if not dry_run:
        collection, _ = Collection.objects.get_or_create(
            slug=collection_slug,
            defaults={"name": collection_slug.capitalize(), "status": "active"},
        )

    job = None
    if not dry_run:
        job = ImportJob.objects.create(
            collection=collection,
            params={"limit": limit, "qid": qid, "dry_run": dry_run},
            status="running",
            progress={"done": 0, "total": limit if not qid else 1},
        )
        job.started_at = timezone.now()
        job.save(update_fields=["started_at"])

    errors: list[str] = []
    done = 0

    try:
        qids = [qid] if qid else client.fetch_football_qids(limit)
    except Exception as e:
        errors.append(f"liste QID: {e}")
        qids = []

    for i in range(0, len(qids), 50):
        batch = qids[i : i + 50]
        try:
            entities = client.fetch_entities(batch)
        except Exception as e:
            errors.append(f"batch {batch[0]}: {e}")
            # Tente un par un pour sauver la progression (reprise partielle).
            entities = []
            for single in batch:
                try:
                    entities.extend(client.fetch_entities([single]))
                except Exception as e2:
                    errors.append(f"{single}: {e2}")
        for data in entities:
            if dry_run:
                done += 1
                continue
            with transaction.atomic():
                ent, _ = EncyclopediaEntity.objects.update_or_create(
                    wikidata_id=data["wikidata_id"],
                    defaults={
                        "label_fr": data.get("label_fr", "")[:300],
                        "description_fr": data.get("description_fr", ""),
                        "wikipedia_url_fr": data.get("wikipedia_url_fr", ""),
                        "props": data.get("props", {}),
                        "image_url": data.get("image_url", ""),
                        "image_attribution": data.get("image_attribution", ""),
                        "pageviews_60d": data.get("pageviews_60d"),
                        "synced_at": timezone.now(),
                    },
                )
                Card.objects.get_or_create(collection=collection, entity=ent)
            done += 1
            if done % 10 == 0 and job:
                job.progress = {"done": done, "total": len(qids)}
                job.errors = errors
                job.save(update_fields=["progress", "errors"])

    if not dry_run:
        # Rareté auto après import (respecte verrous).
        try:
            from cards.models import Rarity
            from cards.services import RarityAssignmentService

            defaults = [
                ("common", "Commune", "#9ca3af", 55, 5, 1),
                ("uncommon", "Peu commune", "#22c55e", 25, 15, 2),
                ("rare", "Rare", "#3b82f6", 12, 50, 3),
                ("epic", "Épique", "#a855f7", 6, 150, 4),
                ("legendary", "Légendaire", "#f59e0b", 2, 500, 5),
            ]
            for code, name, color, weight, sale, order in defaults:
                Rarity.objects.get_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "color": color,
                        "draw_weight": weight,
                        "sale_value": sale,
                        "order": order,
                    },
                )
            if Card.objects.filter(collection=collection).exists():
                RarityAssignmentService().assign_collection(collection)
        except Exception as e:
            errors.append(f"rarity: {e}")
        job.progress = {"done": done, "total": len(qids)}
        job.errors = errors
        job.status = "failed" if errors and done == 0 else "done"
        job.finished_at = timezone.now()
        job.save(update_fields=["progress", "errors", "status", "finished_at"])
        return job
    return None
