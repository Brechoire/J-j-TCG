"""Tirages gratuits : atomiques, idempotents, cooldown global."""

import random

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from core import constants


class CooldownNotReady(Exception):
    def __init__(self, next_available):
        self.next_available = next_available
        super().__init__(f"Prochain booster gratuit : {next_available}")


class NotEnoughCards(Exception):
    """Pas assez de cartes éligibles (ex. pack trop petit pour 5 distinctes)."""

    def __init__(self, needed, found, label="ce périmètre"):
        self.needed = needed
        self.found = found
        self.label = label
        super().__init__(f"{label} : {found} carte(s) éligible(s), {needed} requises.")


class BoosterOpeningService:
    def open_free(self, player, collection, idempotency_key, pack=None):
        from accounts.models import PlayerProfile
        from boosters.models import BoosterOpening, BoosterOpeningCard
        from inventory.models import InventoryEntry

        # Idempotence d'abord : résultat conservé même si navigateur fermé.
        existing = BoosterOpening.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing

        profile, _ = PlayerProfile.objects.get_or_create(user=player)
        now = timezone.now()
        self._check_cooldown(profile, now)

        with transaction.atomic():
            # Verrou ligne (Postgres) ; no-op SQLite, même code, limite documentée.
            profile = PlayerProfile.objects.select_for_update().get(pk=profile.pk)
            self._check_cooldown(profile, timezone.now())
            existing = BoosterOpening.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing

            eligible_ids = None
            if pack is not None:
                from collection.packs import pack_card_ids

                eligible_ids = pack_card_ids(pack)
            picked = self._draw_cards(
                collection,
                constants.BOOSTER_SIZE,
                eligible_ids=eligible_ids,
                label=f"pack {pack.name}" if pack is not None else "cette collection",
            )
            opening = BoosterOpening.objects.create(
                player=player,
                collection=collection,
                kind=BoosterOpening.Kind.FREE,
                idempotency_key=idempotency_key,
                result_cache={"card_ids": [c.pk for c in picked]},
                pack=pack,
            )
            for pos, card in enumerate(picked, start=1):
                BoosterOpeningCard.objects.create(opening=opening, card=card, position=pos)
            for card in picked:
                entry, created = InventoryEntry.objects.get_or_create(
                    player=player, card=card, defaults={"quantity": 1}
                )
                if not created:
                    InventoryEntry.objects.filter(pk=entry.pk).update(quantity=F("quantity") + 1)
            PlayerProfile.objects.filter(pk=profile.pk).update(
                last_free_opened_at=timezone.now(),
                total_opened=F("total_opened") + 1,
            )
            return opening

    @staticmethod
    def _check_cooldown(profile, now):
        last = profile.last_free_opened_at
        if last:
            elapsed = (now - last).total_seconds()
            if elapsed < constants.FREE_BOOSTER_COOLDOWN_SECONDS:
                raise CooldownNotReady(
                    last + timezone.timedelta(seconds=constants.FREE_BOOSTER_COOLDOWN_SECONDS)
                )

    @staticmethod
    def _draw_cards(collection, size: int, eligible_ids=None, label="cette collection"):
        from cards.models import Card

        qs = Card.objects.filter(collection=collection, is_active=True, rarity__isnull=False)
        if eligible_ids is not None:
            qs = qs.filter(pk__in=eligible_ids)
        eligible = list(qs.select_related("rarity"))
        if len(eligible) < size:
            raise NotEnoughCards(needed=size, found=len(eligible), label=label)
        rng = random.SystemRandom()
        picked = []
        picked_ids = set()
        pool = [c for c in eligible]
        for _ in range(size):
            # Poids restants par rareté encore éligible (redistribution prorata).
            by_rarity: dict[str, list] = {}
            for c in pool:
                if c.pk in picked_ids:
                    continue
                by_rarity.setdefault(c.rarity.code, []).append(c)
            if not by_rarity:
                raise ValueError("Plus de cartes éligibles")
            weights = []
            codes = []
            for code, cards in by_rarity.items():
                weights.append(cards[0].rarity.draw_weight)
                codes.append(code)
            chosen_code = rng.choices(codes, weights=weights, k=1)[0]
            chosen = rng.choice(by_rarity[chosen_code])
            picked.append(chosen)
            picked_ids.add(chosen.pk)
        return picked
