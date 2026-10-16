"""Données album : progression uniques, filtres, recherche, compteurs d'onglets."""


def get_album_data(player, collection, rarity_code=None, q=None, box="all"):
    from cards.models import Card

    qs = (
        Card.objects.filter(collection=collection, is_active=True)
        .select_related("entity", "rarity", "auto_rarity")
        .order_by("entity__label_fr")
    )
    if rarity_code:
        qs = qs.filter(rarity__code=rarity_code)
    if q:
        qs = qs.filter(entity__label_fr__icontains=q)
    cards = list(qs)

    from inventory.models import InventoryEntry

    owned = {
        e.card_id: e.quantity
        for e in InventoryEntry.objects.filter(player=player, card__in=[c.pk for c in cards])
    }
    # Compteurs sur le périmètre filtré (rarity+q), avant filtre d'onglet.
    owned_count = sum(1 for c in cards if owned.get(c.pk, 0) > 0)
    missing_count = len(cards) - owned_count
    duplicates_count = sum(1 for c in cards if owned.get(c.pk, 0) >= 2)

    rows = []
    for c in cards:
        qty = owned.get(c.pk, 0)
        if box == "missing" and qty > 0:
            continue
        if box in ("discovered", "owned") and qty == 0:
            continue
        if box == "duplicates" and qty < 2:
            continue
        rows.append({"card": c, "quantity": qty, "discovered": qty > 0})

    total_all = Card.objects.filter(collection=collection, is_active=True).count()
    discovered_all = (
        InventoryEntry.objects.filter(player=player, card__collection=collection)
        .values("card")
        .distinct()
        .count()
    )
    completion_pct = round(discovered_all / total_all * 100) if total_all else 0
    return {
        "cards": rows,
        "total": len(rows) if (rarity_code or q or box != "all") else total_all,
        "discovered": discovered_all,
        "completion_pct": completion_pct,
        # Compteurs d'onglets (périmètre filtré) + progression globale.
        "owned": owned_count,
        "missing": missing_count,
        "duplicates": duplicates_count,
        "total_all": total_all,
        "discovered_all": discovered_all,
    }
