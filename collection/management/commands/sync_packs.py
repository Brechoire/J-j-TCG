"""Crée/met à jour les packs Nationalité/Club depuis les props importées.

Les règles vivent dans `Pack.filter_params` et sont évaluées à la lecture :
aucune donnée redondante, les futurs imports rejoignent seuls les packs.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Synchronise les packs Nationalité/Club d'une collection (règles, pas de doublons)."

    def add_arguments(self, parser):
        from core.constants import BOOSTER_SIZE

        parser.add_argument("collection", help="Slug de la collection (ex. football)")
        parser.add_argument(
            "--min-cards",
            type=int,
            default=BOOSTER_SIZE,
            help=(
                "Ignore les valeurs vues sur moins de N cartes "
                "(défaut : taille du booster, un pack plus petit "
                "ne peut pas s'ouvrir)."
            ),
        )
        parser.add_argument("--dry-run", action="store_true", help="Affiche sans rien créer.")

    def handle(self, *args, **options):
        from cards.country_flags import is_qid, normalize
        from collection.models import Collection, Pack

        col = Collection.objects.get(slug=options["collection"])
        kinds = (("nationality", Pack.Kind.NATIONALITY), ("club", Pack.Kind.CLUB))
        created = updated = 0
        for prop, kind in kinds:
            seen: dict[str, str] = {}
            cards = (
                col.cards.filter(is_active=True)
                .select_related("entity")
                .only("id", "entity__props")
            )
            for card in cards:
                raw = (getattr(card.entity, "props", None) or {}).get(prop) or ""
                if not raw or is_qid(raw):
                    continue
                key = normalize(raw)
                if key and key not in seen:
                    seen[key] = raw.strip()
            for _key, label in sorted(seen.items(), key=lambda kv: kv[1].lower()):
                slug = f"{kind}-{self._slug(label)}"
                count = sum(
                    1
                    for card in cards
                    if normalize((getattr(card.entity, "props", None) or {}).get(prop) or "")
                    == _key
                )
                if count < options["min_cards"]:
                    continue
                if options["dry_run"]:
                    self.stdout.write(f"[{kind}] {label} ({count} cartes)")
                    continue
                _pack, was_created = Pack.objects.update_or_create(
                    collection=col,
                    slug=slug,
                    defaults={
                        "name": label,
                        "kind": kind,
                        "filter_params": {prop: label},
                        "is_active": True,
                    },
                )
                created += was_created
                updated += not was_created
        if options["dry_run"]:
            self.stdout.write("dry-run OK (rien créé)")
        else:
            self.stdout.write(f"packs : {created} créés, {updated} à jour")

    @staticmethod
    def _slug(label: str) -> str:
        from django.utils.text import slugify

        return slugify(label, allow_unicode=False) or "pack"
