import uuid

from django.test import TestCase
from django.urls import reverse


class UserModelTests(TestCase):
    def test_user_has_uuid_pk(self):
        from accounts.models import User

        user = User.objects.create_user(username="ash", email="ash@example.com", password="x" * 12)
        assert isinstance(user.pk, uuid.UUID)

    def test_username_and_email_unique(self):
        from django.db import IntegrityError

        from accounts.models import User

        User.objects.create_user(username="misty", email="misty@example.com", password="x" * 12)
        with self.assertRaises(IntegrityError):
            User.objects.create_user(username="misty", email="other@example.com", password="x" * 12)


class SignupViewTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        url = reverse("accounts:signup")
        response = self.client.post(
            url,
            {
                "username": "brock",
                "email": "brock@example.com",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
            },
        )
        assert response.status_code == 302
        from accounts.models import User

        assert User.objects.filter(username="brock").exists()
        # logged in -> profile page reachable
        profile_url = reverse("accounts:profile")
        response = self.client.get(profile_url)
        assert response.status_code == 200


class CoreConstantsTests(TestCase):
    def test_gameplay_constants(self):
        from core import constants

        assert constants.FREE_BOOSTER_COOLDOWN_SECONDS == 600
        assert constants.BOOSTER_PRICE == 250
        assert constants.BOOSTER_SIZE == 5
