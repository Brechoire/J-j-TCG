from django.test import TestCase


class FakeClient:
    def __init__(self, fail_on_qids=None, timeout_qids=None):
        self.fail_on_qids = set(fail_on_qids or [])
        self.timeout_qids = set(timeout_qids or [])
        self.calls = []

    def fetch_football_qids(self, limit):
        self.calls.append(("qids", limit))
        return [f"Q{9000 + i}" for i in range(limit)]

    def fetch_entities(self, qids):
        from requests import Timeout

        self.calls.append(("entities", tuple(qids)))
        out = []
        for q in qids:
            if q in self.timeout_qids:
                raise Timeout(f"timeout {q}")
            if q in self.fail_on_qids:
                raise ValueError(f"bad {q}")
            i = int(q[1:]) - 9000
            out.append(
                {
                    "wikidata_id": q,
                    "label_fr": f"Joueur {i}",
                    "description_fr": "Footballeur",
                    "wikipedia_url_fr": f"https://fr.wikipedia.org/wiki/Joueur_{i}",
                    "props": {"club": "FC Test", "poste": "Attaquant"},
                    "image_url": "https://commons.example/img.jpg",
                    "image_attribution": "Auteur, CC BY-SA",
                    "pageviews_60d": 5000 - i * 10,
                }
            )
        return out


class FootballImportTests(TestCase):
    def test_dry_run_creates_nothing(self):
        from cards.models import Card
        from encyclopedia.importer import run_football_import
        from encyclopedia.models import EncyclopediaEntity

        run_football_import(collection_slug="football", limit=5, dry_run=True, client=FakeClient())
        assert EncyclopediaEntity.objects.count() == 0
        assert Card.objects.count() == 0

    def test_import_creates_entities_cards_and_rarity(self):
        from cards.models import Card
        from encyclopedia.importer import run_football_import
        from encyclopedia.models import EncyclopediaEntity

        job = run_football_import(collection_slug="football", limit=10, client=FakeClient())
        assert EncyclopediaEntity.objects.count() == 10
        assert Card.objects.count() == 10
        assert job.status == "done"
        assert Card.objects.filter(rarity__isnull=False).count() == 10

    def test_incremental_no_duplicates(self):
        from encyclopedia.importer import run_football_import
        from encyclopedia.models import EncyclopediaEntity

        run_football_import(collection_slug="football", limit=5, client=FakeClient())
        run_football_import(collection_slug="football", limit=5, client=FakeClient())
        assert EncyclopediaEntity.objects.count() == 5

    def test_timeout_logged_and_progress_saved(self):
        from encyclopedia.importer import run_football_import
        from encyclopedia.models import ImportJob

        client = FakeClient(timeout_qids={"Q9001"})
        job = run_football_import(collection_slug="football", limit=3, client=client)
        assert job.status in ("done", "failed")
        assert len(job.errors) >= 1
        assert ImportJob.objects.filter(pk=job.pk).exists()

    def test_reimport_single_qid(self):
        from encyclopedia.importer import run_football_import
        from encyclopedia.models import EncyclopediaEntity

        run_football_import(collection_slug="football", limit=3, client=FakeClient())
        e = EncyclopediaEntity.objects.get(wikidata_id="Q9000")
        e.label_fr = "Vieux nom"
        e.save()
        run_football_import(collection_slug="football", limit=3, qid="Q9000", client=FakeClient())
        e.refresh_from_db()
        assert e.label_fr == "Joueur 0"
