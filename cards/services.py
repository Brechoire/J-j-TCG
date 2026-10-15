"""Service d'attribution automatique de rareté (hybride)."""

import math

CATALOGUE_TARGETS = [
    ("legendary", 0.02),
    ("epic", 0.06),
    ("rare", 0.12),
    ("uncommon", 0.25),
    ("common", 0.55),
]


class RarityAssignmentService:
    @staticmethod
    def compute_auto_score(entity) -> float:
        score, _ = RarityAssignmentService.compute_auto_score_with_signal(entity)
        return score

    @staticmethod
    def compute_auto_score_with_signal(entity) -> tuple[float, bool]:
        pageviews = getattr(entity, "pageviews_60d", None)
        low_signal = pageviews is None
        base = math.log1p(pageviews) if pageviews else 0.0
        has_image = bool(getattr(entity, "image_url", ""))
        has_desc = bool(getattr(entity, "description_fr", ""))
        props = getattr(entity, "props", None) or {}
        has_club = bool(props.get("club"))
        score = base + 0.5 * has_image + 0.3 * has_desc + 0.2 * has_club
        return score, low_signal

    def assign_collection(self, collection) -> dict[str, int]:
        from cards.models import Card, Rarity

        rarities = {r.code: r for r in Rarity.objects.filter(is_active=True)}
        missing = [code for code, _ in CATALOGUE_TARGETS if code not in rarities]
        if missing:
            raise ValueError(f"Raretés manquantes : {missing}")

        cards = list(Card.objects.filter(collection=collection).select_related("entity"))
        scored = [(c, self.compute_auto_score(c.entity)) for c in cards]
        scored.sort(key=lambda t: t[1], reverse=True)

        n = len(scored)
        counts = self._split_counts(n)
        idx = 0
        result: dict[str, int] = {}
        for (code, _), count in zip(CATALOGUE_TARGETS, counts, strict=False):
            for c, score in scored[idx : idx + count]:
                c.auto_score = score
                c.auto_rarity = rarities[code]
                if not c.is_locked:
                    c.rarity = rarities[code]
                c.save(update_fields=["auto_score", "auto_rarity", "rarity"])
            result[code] = count
            idx += count
        return result

    @staticmethod
    def _split_counts(n: int) -> list[int]:
        if n == 0:
            return [0, 0, 0, 0, 0]
        raw = [n * pct for _, pct in CATALOGUE_TARGETS]
        counts = [int(x) for x in raw]
        remainder = n - sum(counts)
        fracs = sorted(range(len(raw)), key=lambda i: raw[i] - counts[i], reverse=True)
        for i in range(remainder):
            counts[fracs[i % len(fracs)]] += 1
        return counts
