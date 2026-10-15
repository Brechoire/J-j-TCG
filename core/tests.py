from django.test import TestCase


class CoreConstantsTests(TestCase):
    def test_gameplay_constants(self):
        from core import constants

        assert constants.FREE_BOOSTER_COOLDOWN_SECONDS == 600
        assert constants.BOOSTER_PRICE == 250
        assert constants.BOOSTER_SIZE == 5
