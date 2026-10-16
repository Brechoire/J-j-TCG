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

    def test_tab_counters(self):
        from inventory.services import get_album_data

        user, col, _ = make_album_world()
        data = get_album_data(user, col)
        assert data["owned"] == 2
        assert data["missing"] == 4
        assert data["duplicates"] == 1
        assert data["total_all"] == 6
        assert data["discovered_all"] == 2

    def test_owned_alias_matches_discovered(self):
        from inventory.services import get_album_data

        user, col, _ = make_album_world()
        owned = get_album_data(user, col, box="owned")
        discovered = get_album_data(user, col, box="discovered")
        assert owned["total"] == discovered["total"] == 2


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

    def test_collection_detail_shows_ownership(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("collection:detail", args=[col.slug]))
        assert r.status_code == 200
        assert "possédées" in r.text
        assert "À découvrir" in r.text
        assert "img/pack-football-legends.jpg" in r.text

    def test_card_detail_shows_packs(self):
        from collection.models import Pack
        from collection.packs import packs_for_card

        user, col, cards = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        pack = Pack.objects.create(
            collection=col, name="Rares", slug="rares", kind=Pack.Kind.SEASON
        )
        pack.cards.add(cards[0])
        r = self.client.get(reverse("inventory:card-detail", args=[col.slug, cards[0].pk]))
        assert r.status_code == 200
        assert "Packs" in r.text
        assert pack.name in r.text
        assert packs_for_card(cards[0], [pack])

    def test_collection_detail_shows_pack_chips(self):
        from collection.models import Pack

        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        Pack.objects.create(collection=col, name="Rares", slug="rares", kind=Pack.Kind.CUSTOM)
        r = self.client.get(reverse("collection:detail", args=[col.slug]))
        assert r.status_code == 200
        assert "Choisir un pack" in r.text
        assert "Rares" in r.text
        r = self.client.get(reverse("collection:detail", args=[col.slug]) + "?pack=rares")
        assert "Ouvrir un booster Rares" in r.text

    def test_album_tabs_render_counts(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:album", args=[col.slug]))
        assert r.status_code == 200
        assert "Mes cartes" in r.text
        assert "À découvrir" in r.text


class InventoryListSortTests(TestCase):
    def test_list_renders_sort_control(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:list"))
        assert r.status_code == 200
        assert 'name="sort"' in r.text
        assert "Rareté" in r.text

    def test_sort_rarity_desc_rarest_first(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:list") + "?sort=rarity_desc")
        assert r.status_code == 200
        # cards[0] = rare « Zidane 0 », cards[2] = commune « Joueur 2 ».
        assert r.text.index("Zidane 0") < r.text.index("Joueur 2")

    def test_sort_rarity_asc_commons_first(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:list") + "?sort=rarity_asc")
        assert r.status_code == 200
        assert r.text.index("Joueur 2") < r.text.index("Zidane 0")

    def test_sort_name_and_invalid_fallback(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:list") + "?sort=name")
        assert r.status_code == 200
        assert r.text.index("Joueur 2") < r.text.index("Zidane 0")

        r = self.client.get(reverse("inventory:list") + "?sort=bogus")
        assert r.status_code == 200

    def test_filter_rarity_keeps_only_matching(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:list") + "?rarity=rare")
        assert r.status_code == 200
        assert "Zidane 0" in r.text
        assert "Joueur 2" not in r.text

    def test_filter_invalid_rarity_ignored(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:list") + "?rarity=bogus")
        assert r.status_code == 200
        assert "Zidane 0" in r.text
        assert "Joueur 2" in r.text

    def test_chips_show_counts_and_preserve_sort(self):
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:list") + "?sort=name")
        assert r.status_code == 200
        assert "R · 1" in r.text
        assert "Toutes · 2" in r.text
        assert "?rarity=rare&amp;sort=name" in r.text

    def test_filter_empty_rarity_offers_reset(self):
        from cards.models import Rarity

        Rarity.objects.get_or_create(
            code="epic",
            defaults={
                "name": "Épique",
                "color": "#000",
                "draw_weight": 6,
                "sale_value": 50,
                "order": 4,
            },
        )
        user, col, _ = make_album_world()
        self.client.force_login(user)
        from django.urls import reverse

        r = self.client.get(reverse("inventory:list") + "?rarity=epic")
        assert r.status_code == 200
        assert "Aucune carte de cette rareté" in r.text
        assert "Voir toutes mes cartes" in r.text
