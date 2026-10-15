from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Importe des footballeurs Wikidata (max 100 requêtes/run initial)."

    def add_arguments(self, parser):
        parser.add_argument("collection", nargs="?", default="football")
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--qid", type=str, default=None)
        parser.add_argument("--resume", action="store_true")

    def handle(self, *args, **options):
        from encyclopedia.importer import run_football_import

        limit = min(int(options["limit"]), 100)
        job = run_football_import(
            collection_slug=options["collection"],
            limit=limit,
            dry_run=options["dry_run"],
            qid=options["qid"],
        )
        if options["dry_run"]:
            self.stdout.write("dry-run OK (rien créé)")
        else:
            self.stdout.write(
                f"job {job.pk} {job.status} : {job.progress} erreurs={len(job.errors)}"
            )
