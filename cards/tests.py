from django.db import IntegrityError
from django.test import TestCase


def make_setup(n=100):
    from cards.models import Card, Rarity
    from collection.models import Collection
    from encyclopedia.models import EncyclopediaEntity

    col = Collection.objects.create(name="Football", slug="football", status="active")
    for r in [
        ("common", "Commune", "#9ca3af", 55, 5, 1),
        ("uncommon", "Peu commune", "#22c55e", 25, 15, 2),
        ("rare", "Rare", "#3b82f6", 12, 50, 3),
        ("epic", "Épique", "#a855f7", 6, 150, 4),
        ("legendary", "Légendaire", "#f59e0b", 2, 500, 5),
    ]:
        Rarity.objects.create(
            code=r[0], name=r[1], color=r[2], draw_weight=r[3], sale_value=r[4], order=r[5]
        )
    for i in range(n):
        ent = EncyclopediaEntity.objects.create(
            wikidata_id=f"Q{1000 + i}",
            label_fr=f"Joueur {i}",
            pageviews_60d=(n - i) * 1000,
            image_url="http://example.com/img.jpg" if i % 2 == 0 else "",
            description_fr="desc" if i % 3 != 0 else "",
        )
        Card.objects.create(collection=col, entity=ent)
    return col


class CardModelTests(TestCase):
    def test_card_unique_collection_entity(self):
        from cards.models import Card
        from collection.models import Collection
        from encyclopedia.models import EncyclopediaEntity

        col = Collection.objects.create(name="Football", slug="football")
        ent = EncyclopediaEntity.objects.create(wikidata_id="Q99", label_fr="X")
        Card.objects.create(collection=col, entity=ent)
        with self.assertRaises(IntegrityError):
            Card.objects.create(collection=col, entity=ent)


class RarityAssignmentTests(TestCase):
    def test_compute_auto_score_uses_pageviews_and_completeness(self):
        from cards.services import RarityAssignmentService
        from encyclopedia.models import EncyclopediaEntity

        full = EncyclopediaEntity(
            wikidata_id="Q1", pageviews_60d=100000, image_url="u", description_fr="d"
        )
        empty = EncyclopediaEntity(wikidata_id="Q2")
        assert RarityAssignmentService.compute_auto_score(full) > (
            RarityAssignmentService.compute_auto_score(empty) or 0
        )

    def test_fallback_without_pageviews(self):
        from cards.services import RarityAssignmentService
        from encyclopedia.models import EncyclopediaEntity

        e = EncyclopediaEntity(wikidata_id="Q3", label_fr="Sans stats")
        score, low_signal = RarityAssignmentService.compute_auto_score_with_signal(e)
        assert low_signal is True
        assert score >= 0

    def test_distribution_catalogue_55_25_12_6_2(self):
        from cards.models import Card
        from cards.services import RarityAssignmentService

        col = make_setup(100)
        RarityAssignmentService().assign_collection(col)
        counts = {}
        for c in Card.objects.filter(collection=col).select_related("auto_rarity"):
            counts[c.auto_rarity.code] = counts.get(c.auto_rarity.code, 0) + 1
        assert counts.get("common") == 55
        assert counts.get("uncommon") == 25
        assert counts.get("rare") == 12
        assert counts.get("epic") == 6
        assert counts.get("legendary") == 2

    def test_locked_rarity_preserved(self):
        from cards.models import Card
        from cards.services import RarityAssignmentService

        col = make_setup(20)
        card = Card.objects.filter(collection=col).first()
        card.is_locked = True
        card.is_manual_override = True
        from cards.models import Rarity

        leg = Rarity.objects.get(code="legendary")
        card.rarity = leg
        card.save()
        RarityAssignmentService().assign_collection(col)
        card.refresh_from_db()
        assert card.rarity.code == "legendary"
        assert card.is_locked is True
