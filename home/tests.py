from django.test import TestCase
from django.urls import reverse


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

    def test_home_contains_title_and_heading(self):
        response = self.client.get(reverse("home:index"))
        assert "Bienvenue" in response.text
        assert "<title>Accueil" in response.text

    def test_home_links_to_tirage(self):
        response = self.client.get(reverse("home:index"))
        assert "/collections/" in response.text
        assert "/collections/football/" in response.text
        assert "Ouvrir un booster" in response.text
