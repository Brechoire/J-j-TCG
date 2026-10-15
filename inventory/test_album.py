import uuid

from django.test import TestCase


def make_album_world():
    from accounts.models import User
    from cards.models import Card, Rarity
    from collection.models import Collection
    from encyclopedia.models import EncyclopediaEntity
    from inventory.models import InventoryEntry

    user = User.objects.create_user(
        username=f"al_{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex}@ex.com",
        password="x" * 12,
    )
    col = Collection.objects.create(
        name="Football", slug=f"fb-{uuid.uuid4().hex[:8]}", status="active"
    )
    rar_common, _ = Rarity.objects.get_or_create(
        code="common",
        defaults={
            "name": "Commune",
            "color": "#000",
            "draw_weight": 55,
            "sale_value": 5,
            "order": 1,
        },
    )
    rar_rare, _ = Rarity.objects.get_or_create(
        code="rare",
        defaults={"name": "Rare", "color": "#00f", "draw_weight": 12, "sale_value": 50, "order": 3},
    )
    cards = []
    for i in range(6):
        ent = EncyclopediaEntity.objects.create(
            wikidata_id=f"QA{i}_{uuid.uuid4().hex[:6]}",
            label_fr=f"Zidane {i}" if i < 2 else f"Joueur {i}",
        )
        c = Card.objects.create(
            collection=col,
            entity=ent,
            rarity=rar_rare if i < 2 else rar_common,
        )
        cards.append(c)
    # possède 2/6 (1 doublon x2)
    InventoryEntry.objects.create(player=user, card=cards[0], quantity=2)
    InventoryEntry.objects.create(player=user, card=cards[2], quantity=1)
    return user, col, cards


class AlbumServiceTests(TestCase):
    def test_progression_counts_uniques(self):
        from inventory.services import get_album_data

        user, col, _ = make_album_world()
        data = get_album_data(user, col)
        assert data["total"] == 6
        assert data["discovered"] == 2
        assert data["completion_pct"] == 33

    def test_filter_rarity(self):
        from inventory.services import get_album_data

        user, col, _ = make_album_world()
        data = get_album_data(user, col, rarity_code="rare")
        assert data["total"] == 2

    def test_search_by_name(self):
        from inventory.services import get_album_data

        user, col, _ = make_album_world()
        data = get_album_data(user, col, q="Zidane")
        assert data["total"] == 2

    def test_missing_and_duplicates(self):
        from inventory.services import get_album_data

        user, col, _ = make_album_world()
        missing = get_album_data(user, col, box="missing")
        assert missing["total"] == 4
        dups = get_album_data(user, col, box="duplicates")
        assert dups["total"] == 1


class AlbumViewsTests(TestCase):
    def test_album_page_200(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:album", args=[col.slug]))
        assert r.status_code == 200

    def test_card_detail_shows_quantity(self):
        user, col, cards = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:card-detail", args=[col.slug, cards[0].pk]))
        assert r.status_code == 200
        assert "2" in r.text

    def test_collections_list_and_detail(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        assert self.client.get(reverse("collection:list")).status_code == 200
        assert self.client.get(reverse("collection:detail", args=[col.slug])).status_code == 200
