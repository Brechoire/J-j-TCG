import uuid

from django.test import TestCase
from django.urls import reverse


def make_player_data(username):
    """Un joueur avec cartes, tirages et stats non nulles."""
    from accounts.models import PlayerProfile, User
    from boosters.models import BoosterOpening
    from cards.models import Card, Rarity
    from collection.models import Collection
    from encyclopedia.models import EncyclopediaEntity
    from inventory.models import InventoryEntry

    u = User.objects.create_user(
        username=username, email=f"{username}@ex.com", password="x" * 12
    )
    col = Collection.objects.create(
        name=f"C {uuid.uuid4().hex[:6]}",
        slug=f"c-{uuid.uuid4().hex[:8]}",
        status="active",
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
    ent = EncyclopediaEntity.objects.create(wikidata_id=f"QR{uuid.uuid4().hex[:8]}")
    card = Card.objects.create(collection=col, entity=ent, rarity=rar)
    InventoryEntry.objects.create(player=u, card=card, quantity=3)
    BoosterOpening.objects.create(
        player=u, collection=col, idempotency_key=uuid.uuid4()
    )
    PlayerProfile.objects.update_or_create(
        user=u,
        defaults={"total_opened": 2, "unique_discovered": 1},
    )
    return u


# TODO TEMP (dev) : tests du reset à SUPPRIMER avec la vue avant prod.
class ResetCollectionTests(TestCase):
    def test_post_wipes_player_side(self):
        from accounts.models import PlayerProfile
        from boosters.models import BoosterOpening
        from inventory.models import InventoryEntry

        u = make_player_data("reset1")
        self.client.force_login(u)
        response = self.client.post(reverse("inventory:reset"))
        assert response.status_code == 302
        assert InventoryEntry.objects.filter(player=u).count() == 0
        assert BoosterOpening.objects.filter(player=u).count() == 0
        profile = PlayerProfile.objects.get(user=u)
        assert profile.total_opened == 0
        assert profile.unique_discovered == 0
        assert profile.last_free_opened_at is None

    def test_get_not_allowed(self):
        from accounts.models import User

        u = User.objects.create_user(
            username="reset2", email="reset2@ex.com", password="x" * 12
        )
        self.client.force_login(u)
        assert self.client.get(reverse("inventory:reset")).status_code == 405

    def test_login_required(self):
        response = self.client.post(reverse("inventory:reset"))
        assert response.status_code == 302
        assert "login" in response["Location"] or "connexion" in response["Location"]
