import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone


def make_world(n_cards=20):
    from accounts.models import User
    from cards.models import Card, Rarity
    from collection.models import Collection
    from encyclopedia.models import EncyclopediaEntity

    user = User.objects.create_user(
        username=f"u_{uuid.uuid4().hex[:8]}", email=f"{uuid.uuid4().hex}@ex.com", password="x" * 12
    )
    col = Collection.objects.create(
        name=f"F {uuid.uuid4().hex[:6]}", slug=f"f-{uuid.uuid4().hex[:8]}"
    )
    for code, weight in [
        ("common", 55),
        ("uncommon", 25),
        ("rare", 12),
        ("epic", 6),
        ("legendary", 2),
    ]:
        Rarity.objects.get_or_create(
            code=code,
            defaults={
                "name": code,
                "color": "#000",
                "draw_weight": weight,
                "sale_value": 5,
                "order": 1,
            },
        )
    rarities = list(Rarity.objects.all())
    for i in range(n_cards):
        ent = EncyclopediaEntity.objects.create(wikidata_id=f"QW{i}_{uuid.uuid4().hex[:6]}")
        Card.objects.create(collection=col, entity=ent, rarity=rarities[i % len(rarities)])
    return user, col


class FreeBoosterTests(TestCase):
    def test_first_free_immediate(self):
        from boosters.services import BoosterOpeningService

        user, col = make_world()
        opening = BoosterOpeningService().open_free(user, col, idempotency_key=uuid.uuid4())
        assert opening.pk is not None
        assert opening.cards.count() == 5

    def test_five_distinct_cards(self):
        from boosters.services import BoosterOpeningService

        user, col = make_world()
        opening = BoosterOpeningService().open_free(user, col, idempotency_key=uuid.uuid4())
        ids = list(opening.cards.values_list("id", flat=True))
        assert len(ids) == 5
        assert len(set(ids)) == 5

    def test_cooldown_global_blocks_second_open(self):
        from boosters.services import BoosterOpeningService, CooldownNotReady

        user, col = make_world()
        BoosterOpeningService().open_free(user, col, idempotency_key=uuid.uuid4())
        with self.assertRaises(CooldownNotReady):
            BoosterOpeningService().open_free(user, col, idempotency_key=uuid.uuid4())

    def test_cooldown_global_across_collections(self):
        from boosters.services import BoosterOpeningService, CooldownNotReady
        from collection.models import Collection

        user, col = make_world()
        col2 = Collection.objects.create(name="F2", slug=f"f2-{uuid.uuid4().hex[:6]}")
        BoosterOpeningService().open_free(user, col, idempotency_key=uuid.uuid4())
        with self.assertRaises(CooldownNotReady):
            BoosterOpeningService().open_free(user, col2, idempotency_key=uuid.uuid4())

    def test_cooldown_expires_after_10min(self):
        from boosters.services import BoosterOpeningService

        user, col = make_world()
        BoosterOpeningService().open_free(user, col, idempotency_key=uuid.uuid4())
        user.profile.last_free_opened_at = timezone.now() - timedelta(seconds=601)
        user.profile.save()
        opening = BoosterOpeningService().open_free(user, col, idempotency_key=uuid.uuid4())
        assert opening.pk is not None

    def test_idempotent_same_key_no_double(self):
        from boosters.services import BoosterOpeningService
        from inventory.models import InventoryEntry

        user, col = make_world()
        key = uuid.uuid4()
        o1 = BoosterOpeningService().open_free(user, col, idempotency_key=key)
        # reset cooldown pour prouver que c'est bien l'idempotence, pas le cooldown
        user.profile.refresh_from_db()
        user.profile.last_free_opened_at = timezone.now() - timedelta(seconds=601)
        user.profile.save()
        o2 = BoosterOpeningService().open_free(user, col, idempotency_key=key)
        assert o1.pk == o2.pk
        total = sum(InventoryEntry.objects.filter(player=user).values_list("quantity", flat=True))
        assert total == 5

    def test_redistribution_when_rarity_empty(self):
        from accounts.models import User
        from cards.models import Card, Rarity
        from collection.models import Collection
        from encyclopedia.models import EncyclopediaEntity

        user = User.objects.create_user(
            username=f"r_{uuid.uuid4().hex[:8]}",
            email=f"{uuid.uuid4().hex}@ex.com",
            password="x" * 12,
        )
        col = Collection.objects.create(name="Mono", slug=f"mono-{uuid.uuid4().hex[:8]}")
        common, _ = Rarity.objects.get_or_create(
            code="common",
            defaults={
                "name": "Commune",
                "color": "#000",
                "draw_weight": 55,
                "sale_value": 5,
                "order": 1,
            },
        )
        for i in range(10):
            ent = EncyclopediaEntity.objects.create(wikidata_id=f"QM{i}_{uuid.uuid4().hex[:6]}")
            Card.objects.create(collection=col, entity=ent, rarity=common)
        from boosters.services import BoosterOpeningService

        opening = BoosterOpeningService().open_free(user, col, idempotency_key=uuid.uuid4())
        assert opening.cards.count() == 5
