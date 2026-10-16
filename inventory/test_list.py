import uuid

from django.test import TestCase
from django.urls import reverse


def make_setup(username):
    from accounts.models import User
    from cards.models import Card, Rarity
    from collection.models import Collection
    from encyclopedia.models import EncyclopediaEntity
    from inventory.models import InventoryEntry

    u = User.objects.create_user(username=username, email=f"{username}@ex.com", password="x" * 12)
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
    cards = []
    for i, qty in enumerate((1, 3)):
        ent = EncyclopediaEntity.objects.create(
            wikidata_id=f"QD{i}_{uuid.uuid4().hex[:6]}",
            label_fr=f"Carte {'Simple' if qty == 1 else 'Double'} {uuid.uuid4().hex[:4]}",
        )
        card = Card.objects.create(collection=col, entity=ent, rarity=rar)
        InventoryEntry.objects.create(player=u, card=card, quantity=qty)
        cards.append(card)
    return u, cards


class InventoryDoublesFilterTests(TestCase):
    def test_default_shows_all_entries(self):
        u, _ = make_setup("dbl1")
        self.client.force_login(u)
        page = self.client.get(reverse("inventory:list"))
        assert page.status_code == 200
        assert "Doublons uniquement" in page.text
        assert page.text.count("pk-card-link") == 2

    def test_doubles_param_shows_only_duplicates(self):
        u, _ = make_setup("dbl2")
        self.client.force_login(u)
        page = self.client.get(reverse("inventory:list") + "?doubles=1")
        assert page.status_code == 200
        assert "Voir toutes mes cartes" in page.text
        assert page.text.count("pk-card-link") == 1
        assert "Double" in page.text
        assert "Simple" not in page.text

    def test_doubles_empty_state(self):
        from accounts.models import User
        from cards.models import Card, Rarity
        from collection.models import Collection
        from encyclopedia.models import EncyclopediaEntity
        from inventory.models import InventoryEntry

        u = User.objects.create_user(username="dbl3", email="dbl3@ex.com", password="x" * 12)
        col = Collection.objects.create(
            name=f"C {uuid.uuid4().hex[:6]}", slug=f"c-{uuid.uuid4().hex[:8]}"
        )
        rar, _ = Rarity.objects.get_or_create(
            code="common",
            defaults={"name": "C", "color": "#000", "draw_weight": 1, "sale_value": 1, "order": 1},
        )
        ent = EncyclopediaEntity.objects.create(wikidata_id=f"QD_{uuid.uuid4().hex[:6]}")
        card = Card.objects.create(collection=col, entity=ent, rarity=rar)
        InventoryEntry.objects.create(player=u, card=card, quantity=1)
        self.client.force_login(u)
        page = self.client.get(reverse("inventory:list") + "?doubles=1")
        assert "Aucun doublon" in page.text

    def test_doubles_combines_with_rarity(self):
        u, _ = make_setup("dbl4")
        self.client.force_login(u)
        page = self.client.get(reverse("inventory:list") + "?doubles=1&rarity=common")
        assert page.status_code == 200
        assert page.text.count("pk-card-link") == 1
