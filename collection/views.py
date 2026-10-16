from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.views import View

from .models import Collection


class CollectionListView(View):
    def get(self, request):
        cols = list(Collection.objects.filter(status="active").order_by("display_order", "name"))
        col_ids = [c.pk for c in cols]

        from cards.models import Card

        total_map: dict = {}
        if col_ids:
            total_map = dict(
                Card.objects.filter(collection_id__in=col_ids, is_active=True)
                .values("collection_id")
                .annotate(n=Count("id"))
                .values_list("collection_id", "n")
            )

        discovered_map: dict = {}
        if request.user.is_authenticated and col_ids:
            from inventory.models import InventoryEntry

            rows = (
                InventoryEntry.objects.filter(player=request.user, card__collection_id__in=col_ids)
                .values("card__collection_id")
                .annotate(n=Count("card_id", distinct=True))
            )
            discovered_map = {r["card__collection_id"]: r["n"] for r in rows}

        items = []
        for c in cols:
            total = total_map.get(c.pk, 0)
            discovered = discovered_map.get(c.pk, 0)
            items.append(
                {
                    "collection": c,
                    "total": total,
                    "discovered": discovered,
                    "missing": total - discovered,
                    "completion_pct": round(discovered / total * 100) if total else 0,
                }
            )

        return render(
            request,
            "collection/list.html",
            {
                "collections": cols,
                "items": items,
                "total_collections": len(cols),
                "total_cards": sum(total_map.values()),
                # Contexte pour la nav basse (onglet Booster) : thème principal.
                "collection": cols[0] if cols else None,
            },
        )


class CollectionDetailView(View):
    def get(self, request, slug):
        col = get_object_or_404(Collection, slug=slug)
        from cards.models import Card

        cards = list(
            Card.objects.filter(collection=col, is_active=True)
            .select_related("entity", "rarity")
            .order_by("entity__label_fr")
        )
        owned: dict[int, int] = {}
        if request.user.is_authenticated:
            from inventory.models import InventoryEntry

            owned = {
                e.card_id: e.quantity
                for e in InventoryEntry.objects.filter(
                    player=request.user, card__in=[c.pk for c in cards]
                )
            }
        rows = [
            {"card": c, "quantity": owned.get(c.pk, 0), "discovered": owned.get(c.pk, 0) > 0}
            for c in cards
        ]
        discovered = sum(1 for r in rows if r["discovered"])
        total = len(rows)

        from collection.packs import pack_counts

        packs = list(col.packs.filter(is_active=True))
        counts = pack_counts(packs, cards) if packs else {}
        pack_items = [{"pack": p, "total": counts.get(p.pk, 0)} for p in packs]
        selected_pack = None
        pack_slug = request.GET.get("pack", "")
        if pack_slug:
            selected_pack = next((p for p in packs if p.slug == pack_slug), None)
        return render(
            request,
            "collection/detail.html",
            {
                "collection": col,
                "total": total,
                "rows": rows,
                "discovered": discovered,
                "completion_pct": round(discovered / total * 100) if total else 0,
                "pack_items": pack_items,
                "selected_pack": selected_pack,
            },
        )
