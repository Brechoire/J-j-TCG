from django.db import IntegrityError
from django.test import TestCase


class EncyclopediaEntityTests(TestCase):
    def test_wikidata_id_unique(self):
        from encyclopedia.models import EncyclopediaEntity

        EncyclopediaEntity.objects.create(wikidata_id="Q42", label="Douglas Adams")
        with self.assertRaises(IntegrityError):
            EncyclopediaEntity.objects.create(wikidata_id="Q42", label="Doublon")

    def test_minimal_fields(self):
        from encyclopedia.models import EncyclopediaEntity

        e = EncyclopediaEntity.objects.create(
            wikidata_id="Q1",
            label_fr="Test",
            pageviews_60d=123,
        )
        assert e.pk is not None
