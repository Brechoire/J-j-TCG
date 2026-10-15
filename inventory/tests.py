from django.test import TestCase


class InventoryModelTests(TestCase):
    def test_unique_player_card(self):
        from django.db import IntegrityError

        from accounts.models import User
        from cards.models import Card
        from collection.models import Collection
        from encyclopedia.models import EncyclopediaEntity
        from inventory.models import InventoryEntry

        u = User.objects.create_user(username="a1", email="a1@ex.com", password="x" * 12)
        col = Collection.objects.create(name="F", slug="f")
        ent = EncyclopediaEntity.objects.create(wikidata_id="QX1")
        card = Card.objects.create(collection=col, entity=ent)
        InventoryEntry.objects.create(player=u, card=card, quantity=1)
        with self.assertRaises(IntegrityError):
            InventoryEntry.objects.create(player=u, card=card, quantity=1)
