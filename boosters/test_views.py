import uuid

from django.test import TestCase
from django.urls import reverse


def make_collection_with_cards(n=10):
    from cards.models import Card, Rarity
    from collection.models import Collection
    from encyclopedia.models import EncyclopediaEntity

    col = Collection.objects.create(
        name=f"C {uuid.uuid4().hex[:6]}", slug=f"c-{uuid.uuid4().hex[:8]}", status="active"
    )
    rar, _ = Rarity.objects.get_or_create(
        code="common",
        defaults={
            "name": "Commune",
            "color": "#000",
            "draw_weight": 55,
            "sale_value": 5,
            "order": 1,
        },
    )
    for i in range(n):
        ent = EncyclopediaEntity.objects.create(wikidata_id=f"QV{i}_{uuid.uuid4().hex[:6]}")
        Card.objects.create(collection=col, entity=ent, rarity=rar)
    return col


class BoosterViewsTests(TestCase):
    def test_open_free_redirects_to_result(self):
        from accounts.models import User

        u = User.objects.create_user(username="vw1", email="vw1@ex.com", password="x" * 12)
        self.client.force_login(u)
        col = make_collection_with_cards()
        response = self.client.post(reverse("boosters:open", args=[col.slug]))
        assert response.status_code == 302
        assert "/boosters/" in response["Location"]

    def test_history_lists_openings(self):
        from accounts.models import User

        u = User.objects.create_user(username="vw2", email="vw2@ex.com", password="x" * 12)
        self.client.force_login(u)
        col = make_collection_with_cards()
        self.client.post(reverse("boosters:open", args=[col.slug]))
        response = self.client.get(reverse("boosters:history"))
        assert response.status_code == 200
