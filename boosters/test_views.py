import uuid
from pathlib import Path

from django.test import TestCase
from django.urls import reverse


def make_collection_with_cards(n=10, image_url=None):
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
        ent = EncyclopediaEntity.objects.create(
            wikidata_id=f"QV{i}_{uuid.uuid4().hex[:6]}",
            image_url=image_url if i == 0 and image_url else "",
        )
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

    def test_result_reveals_one_by_one_with_new_badges(self):
        from accounts.models import User

        u = User.objects.create_user(username="vw3", email="vw3@ex.com", password="x" * 12)
        self.client.force_login(u)
        col = make_collection_with_cards()
        response = self.client.post(reverse("boosters:open", args=[col.slug]))
        result_url = response["Location"]
        page = self.client.get(result_url)
        assert page.status_code == 200
        assert "data-reveal-deck" in page.text
        assert page.text.count("data-reveal-slot") >= 5
        assert "Révéler la première carte" in page.text
        assert "rarity-badge--common" in page.text

    def test_result_back_stays_pack_visual_until_click(self):
        from accounts.models import User

        u = User.objects.create_user(username="vw4", email="vw4@ex.com", password="x" * 12)
        self.client.force_login(u)
        col = make_collection_with_cards(n=5, image_url="https://example.com/photo.jpg")
        response = self.client.post(reverse("boosters:open", args=[col.slug]))
        page = self.client.get(response["Location"])
        assert page.status_code == 200
        # Aucun teaser par-dessus le visuel pack : le dos reste fixe jusqu'au clic.
        # (La photo reste affichée sur la face une fois révélée.)
        assert "reveal-back__teaser" not in page.text
        assert page.text.count("reveal-slot--common") == 5
        assert "data-reveal-found" in page.text
        assert "data-reveal-found-list" in page.text

    def test_result_pack_intro_before_sequence(self):
        from accounts.models import User

        u = User.objects.create_user(username="vw5", email="vw5@ex.com", password="x" * 12)
        self.client.force_login(u)
        col = make_collection_with_cards(n=5)
        response = self.client.post(reverse("boosters:open", args=[col.slug]))
        page = self.client.get(response["Location"])
        assert page.status_code == 200
        assert "data-pack-intro" in page.text
        assert "img/pack-football-legends.jpg" in page.text
        assert "Ouvrir le pack" in page.text
        assert "js/pack-open.js" in page.text


class PackOpeningTests(TestCase):
    def _pack_world(self, per_nat=6):
        from collection.test_packs import make_pack_world

        return make_pack_world(per_nat=per_nat)

    def test_open_with_pack_records_it(self):
        from accounts.models import User
        from boosters.models import BoosterOpening

        u = User.objects.create_user(username="pk1", email="pk1@ex.com", password="x" * 12)
        self.client.force_login(u)
        col, pack, _ = self._pack_world()
        response = self.client.post(reverse("boosters:open", args=[col.slug]), {"pack": pack.slug})
        assert response.status_code == 302
        opening = BoosterOpening.objects.get(player=u)
        assert opening.pack_id == pack.pk
        page = self.client.get(response["Location"])
        assert pack.name in page.text

    def test_open_unknown_pack_404(self):
        from accounts.models import User

        u = User.objects.create_user(username="pk2", email="pk2@ex.com", password="x" * 12)
        self.client.force_login(u)
        col, _pack, _ = self._pack_world()
        response = self.client.post(reverse("boosters:open", args=[col.slug]), {"pack": "nope"})
        assert response.status_code == 404

    def test_open_too_small_pack_redirects_with_message(self):
        from accounts.models import User

        u = User.objects.create_user(username="pk3", email="pk3@ex.com", password="x" * 12)
        self.client.force_login(u)
        col, pack, _ = self._pack_world(per_nat=1)
        response = self.client.post(reverse("boosters:open", args=[col.slug]), {"pack": pack.slug})
        assert response.status_code == 302
        assert f"?pack={pack.slug}" in response["Location"]
        page = self.client.get(response["Location"])
        assert 'role="alert"' in page.text

    def test_history_shows_pack(self):
        from accounts.models import User

        u = User.objects.create_user(username="pk4", email="pk4@ex.com", password="x" * 12)
        self.client.force_login(u)
        col, pack, _ = self._pack_world()
        self.client.post(reverse("boosters:open", args=[col.slug]), {"pack": pack.slug})
        response = self.client.get(reverse("boosters:history"))
        assert response.status_code == 200
        assert pack.name in response.text


class RevealCssTests(TestCase):
    """Le récapitulatif exige min-width:0 sur la carte (item flex), sinon les
    cartes débordent de leur cellule et se chevauchent. Le CSS compilé doit
    suivre la source (ne pas oublier `npm run build:css`)."""

    def test_all_phase_card_can_shrink(self):
        import re

        base = Path(__file__).resolve().parent.parent / "static"
        src = (base / "src" / "input.css").read_text(encoding="utf-8")
        out = (base / "css" / "output.css").read_text(encoding="utf-8")
        pattern = (
            r'\.reveal-deck\[data-phase="?all"?\] \.reveal-face \.pk-card'
            r"\s*\{[^}]*min-width\s*:\s*0"
        )
        assert re.search(pattern, src), "règle min-width absente de input.css"
        assert re.search(pattern, out), "output.css obsolète : relancer npm run build:css"

    def test_card_back_uses_pack_artwork_and_keeps_halo(self):
        base = Path(__file__).resolve().parent.parent / "static"
        src = (base / "src" / "input.css").read_text(encoding="utf-8")
        out = (base / "css" / "output.css").read_text(encoding="utf-8")
        assert "../img/pack-football-legends.jpg" in src
        assert "../img/pack-football-legends.jpg" in out
        assert (base / "img" / "pack-football-legends.jpg").is_file()
        # Halo lumineux par rareté conservé sur le dos à révéler.
        assert "halo-breathe" in src and "halo-breathe" in out
        assert ".reveal-slot--legendary" in out
