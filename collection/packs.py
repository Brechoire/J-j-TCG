"""Appartenances carte ↔ pack : règles sur props + curation explicite.

Les règles (`Pack.filter_params`, ex. {"nationality": "France"}) sont évaluées
à la lecture : un nouvel import rejoint seul les packs. La comparaison est
normalisée (minuscules, sans accents) via `cards.country_flags.normalize`.
Les membres curés (`Pack.cards`) couvrent les saisons historiques.
"""

RULE_PROPS = ("nationality", "club")


def _norm(value) -> str:
    from cards.country_flags import normalize

    return normalize(value or "")


def _rules(pack) -> dict:
    params = pack.filter_params or {}
    return {k: _norm(params[k]) for k in RULE_PROPS if params.get(k)}


def _rule_match(rules: dict, card) -> bool:
    if not rules:
        return False
    props = getattr(getattr(card, "entity", None), "props", None) or {}
    return all(_norm(props.get(k)) == v for k, v in rules.items())


def explicit_ids_map(packs) -> dict[int, set[int]]:
    """{pack_pk: {card_ids curés}} en une requête pour tous les packs."""
    from collection.models import Pack

    through = Pack.cards.through
    rows = through.objects.filter(pack__in=packs).values_list("pack_id", "card_id")
    out: dict[int, set[int]] = {p.pk: set() for p in packs}
    for pack_id, card_id in rows:
        out.setdefault(pack_id, set()).add(card_id)
    return out


def pack_matches_card(pack, card, explicit_ids: set[int] | None = None) -> bool:
    """Un pack contient-il cette carte (curation OU règles) ?"""
    if explicit_ids is None:
        if pack.cards.filter(pk=card.pk).exists():
            return True
    elif card.pk in explicit_ids:
        return True
    return _rule_match(_rules(pack), card)


def pack_card_ids(pack) -> set[int]:
    """IDs des cartes éligibles d'un pack (explicites + règles)."""
    from cards.models import Card

    ids = set(pack.cards.values_list("pk", flat=True))
    rules = _rules(pack)
    if rules:
        cards = (
            Card.objects.filter(collection=pack.collection, is_active=True)
            .select_related("entity")
            .only("id", "entity__props")
        )
        for card in cards:
            props = getattr(card.entity, "props", None) or {}
            if all(_norm(props.get(k)) == v for k, v in rules.items()):
                ids.add(card.pk)
    return ids


def pack_counts(packs, cards) -> dict[int, int]:
    """{pack_pk: nb de cartes} sur une liste de cartes déjà chargées."""
    ids_map = explicit_ids_map(packs)
    rules = {p.pk: _rules(p) for p in packs}
    counts = {p.pk: 0 for p in packs}
    for card in cards:
        for pack in packs:
            if card.pk in ids_map.get(pack.pk, ()):
                counts[pack.pk] += 1
            elif _rule_match(rules[pack.pk], card):
                counts[pack.pk] += 1
    return counts


def packs_for_card(card, packs, ids_map: dict | None = None) -> list:
    """Packs (parmi `packs`) contenant `card`, ordre d'affichage."""
    if ids_map is None:
        ids_map = explicit_ids_map(packs)
    rules = {p.pk: _rules(p) for p in packs}
    return [p for p in packs if card.pk in ids_map.get(p.pk, ()) or _rule_match(rules[p.pk], card)]
