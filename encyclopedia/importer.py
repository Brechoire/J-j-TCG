"""Import Football incrémental, reprise, dry-run, réimport QID."""

from django.db import transaction
from django.utils import timezone

DEFAULT_IMPORT_CONFIG = {
    "instance_of": "Q5",  # être humain
    "occupation_qid": "Q937857",  # joueur de foot
}


def resolve_import_config(collection) -> dict:
    """Fusionne défauts foot + `Collection.import_config` (admin).

    `occupation_qid: null` explicite = filtre P31 seul (ex. stades).
    `sport_qid` optionnel = filtre P641 (ex. stades de foot : "Q2736").
    Exemples :
    - joueurs : {"instance_of": "Q5", "occupation_qid": "Q937857"}
    - entraîneurs : {"instance_of": "Q5", "occupation_qid": "Q628099"}
    - stades de foot : {"instance_of": "Q483110", "occupation_qid": null,
      "sport_qid": "Q2736"}
    """
    config = dict(DEFAULT_IMPORT_CONFIG)
    stored = getattr(collection, "import_config", None) or {}
    if isinstance(stored, dict):
        if stored.get("instance_of"):
            config["instance_of"] = stored["instance_of"]
        if "occupation_qid" in stored:
            config["occupation_qid"] = stored["occupation_qid"] or None
        if stored.get("sport_qid"):
            config["sport_qid"] = stored["sport_qid"]
    return config


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
    config = dict(DEFAULT_IMPORT_CONFIG)
    if not dry_run:
        collection, created = Collection.objects.get_or_create(
            slug=collection_slug,
            defaults={
                "name": collection_slug.capitalize(),
                "status": "active",
                "import_config": dict(DEFAULT_IMPORT_CONFIG),
            },
        )
        # Collection existante sans config (cas DB vide / pré-migration) :
        # applique les défauts foot pour garder un comportement prévisible.
        if not created and not collection.import_config:
            collection.import_config = dict(DEFAULT_IMPORT_CONFIG)
            collection.save(update_fields=["import_config"])
        config = resolve_import_config(collection)

    job = None
    if not dry_run:
        job = ImportJob.objects.create(
            collection=collection,
            params={"limit": limit, "qid": qid, "dry_run": dry_run, **config},
            status="running",
            progress={"done": 0, "total": limit if not qid else 1},
        )
        job.started_at = timezone.now()
        job.save(update_fields=["started_at"])

    errors: list[str] = []
    done = 0

    try:
        if qid:
            qids = [qid]
        elif hasattr(client, "fetch_qids"):
            qids = client.fetch_qids(limit, **config)
        else:  # clients de test historiques sans fetch_qids
            qids = client.fetch_football_qids(limit)
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
                        "license": data.get("license", ""),
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
