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
        ent = EncyclopediaEntity.objects.create(wikidata_id=f"QH{i}_{uuid.uuid4().hex[:6]}")
        Card.objects.create(collection=col, entity=ent, rarity=rar)
    return col


def make_user(username):
    from accounts.models import User

    return User.objects.create_user(
        username=username, email=f"{username}@ex.com", password="x" * 12
    )


class HomeViewTests(TestCase):
    def test_home_page_returns_200(self):
        response = self.client.get("/")
        assert response.status_code == 200

    def test_home_url_resolves_by_name(self):
        url = reverse("home:index")
        assert url == "/"
        response = self.client.get(url)
        assert response.status_code == 200

    def test_home_uses_correct_templates(self):
        response = self.client.get(reverse("home:index"))
        self.assertTemplateUsed(response, "home/index.html")
        self.assertTemplateUsed(response, "base.html")

    def test_anonymous_sees_welcome_and_signup(self):
        response = self.client.get(reverse("home:index"))
        assert "<title>Accueil" in response.text
        assert "Bienvenue" in response.text
        assert reverse("accounts:signup") in response.text
        assert "/collections/" in response.text

    def test_authenticated_ready_hero_opens_booster(self):
        u = make_user("home1")
        self.client.force_login(u)
        col = make_collection_with_cards()
        response = self.client.get(reverse("home:index"))
        assert response.status_code == 200
        assert "Ouvrir un booster" in response.text
        assert f"/boosters/ouvrir/{col.slug}/" in response.text
        assert "cartes découvertes" in response.text
        assert "img/pack-football-legends.jpg" in response.text

    def test_authenticated_after_open_shows_recent_draws(self):
        u = make_user("home2")
        self.client.force_login(u)
        col = make_collection_with_cards()
        self.client.post(reverse("boosters:open", args=[col.slug]))
        response = self.client.get(reverse("home:index"))
        assert "Derniers tirages" in response.text
        assert "Tout l'historique" in response.text

    def test_authenticated_cooldown_hero_links_album(self):
        u = make_user("home3")
        self.client.force_login(u)
        col = make_collection_with_cards()
        self.client.post(reverse("boosters:open", args=[col.slug]))
        response = self.client.get(reverse("home:index"))
        # 2e visite : cooldown actif (60 s) → pas de formulaire, lien album.
        assert "Ouvrir un booster" not in response.text
        assert f"/albums/{col.slug}/" in response.text
