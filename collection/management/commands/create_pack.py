"""Crée un pack curé (ex. saison historique) depuis une liste de QID.

Exemple :
    python manage.py create_pack football ligue1-2001-2002 "Ligue 1 2001-2002" \\
        --kind season --qids Q123,Q456 --description "..."
"""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crée un pack curé à partir d'une liste de QID Wikidata."

    def add_arguments(self, parser):
        parser.add_argument("collection", help="Slug de la collection")
        parser.add_argument("slug", help="Slug du pack")
        parser.add_argument("name", help="Nom affiché du pack")
        parser.add_argument(
            "--kind",
            default="season",
            choices=["nationality", "club", "season", "custom"],
        )
        parser.add_argument("--qids", default="", help="QID séparés par des virgules")
        parser.add_argument("--description", default="")
        parser.add_argument("--inactive", action="store_true")

    def handle(self, *args, **options):
        from cards.models import Card
        from collection.models import Collection, Pack
        from encyclopedia.models import EncyclopediaEntity

        col = Collection.objects.get(slug=options["collection"])
        pack, _created = Pack.objects.update_or_create(
            collection=col,
            slug=options["slug"],
            defaults={
                "name": options["name"],
                "kind": options["kind"],
                "description": options["description"],
                "is_active": not options["inactive"],
            },
        )
        qids = [q.strip() for q in options["qids"].split(",") if q.strip()]
        entities = EncyclopediaEntity.objects.filter(wikidata_id__in=qids)
        found = {e.wikidata_id for e in entities}
        missing = [q for q in qids if q not in found]
        cards = Card.objects.filter(collection=col, entity__in=entities)
        pack.cards.add(*cards)
        self.stdout.write(
            f"pack {pack.slug} : {cards.count()} carte(s) rattachée(s)"
            + (f" — QID inconnus : {', '.join(missing)}" if missing else "")
        )
        if missing:
            raise CommandError(f"QID inconnus (importez-les d'abord) : {', '.join(missing)}")
