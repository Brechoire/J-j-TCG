import uuid

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from collection.models import Collection

from .models import BoosterOpening
from .services import BoosterOpeningService, CooldownNotReady, NotEnoughCards


@method_decorator(login_required, name="dispatch")
class OpenFreeView(View):
    def post(self, request, slug):
        from django.contrib import messages

        col = get_object_or_404(Collection, slug=slug)
        pack = None
        pack_slug = request.POST.get("pack", "")
        if pack_slug:
            from collection.models import Pack

            pack = get_object_or_404(Pack, collection=col, slug=pack_slug, is_active=True)
        try:
            opening = BoosterOpeningService().open_free(
                request.user, col, idempotency_key=uuid.uuid4(), pack=pack
            )
        except CooldownNotReady as e:
            return render(
                request,
                "boosters/cooldown.html",
                {"next_available": e.next_available, "collection": col},
                status=429,
            )
        except NotEnoughCards as e:
            messages.error(request, str(e))
            url = reverse("collection:detail", args=[col.slug])
            if pack is not None:
                url += f"?pack={pack.slug}"
            return redirect(url)
        return redirect("boosters:result", pk=opening.pk)


@method_decorator(login_required, name="dispatch")
class ResultView(View):
    def get(self, request, pk):
        opening = get_object_or_404(BoosterOpening, pk=pk, player=request.user)
        ocs = list(opening.opening_cards.select_related("card__entity", "card__rarity"))
        from inventory.models import InventoryEntry

        quantities = {
            e.card_id: e.quantity
            for e in InventoryEntry.objects.filter(
                player=request.user, card__in=[oc.card_id for oc in ocs]
            )
        }
        for oc in ocs:
            qty = quantities.get(oc.card_id, 1)
            oc.quantity = qty
            # Après crédit d'ouverture : quantité 1 = toute première découverte.
            oc.is_new = qty <= 1
        # Récapitulatif groupé par rareté (l'ordre de révélation reste la position).
        summary: dict[str, dict] = {}
        for oc in ocs:
            code = oc.card.rarity.code if oc.card.rarity else "common"
            entry = summary.setdefault(
                code,
                {
                    "code": code,
                    "name": oc.card.rarity.name if oc.card.rarity else "Commune",
                    "order": oc.card.rarity.order if oc.card.rarity else 999,
                    "count": 0,
                },
            )
            entry["count"] += 1
        rarity_summary = sorted(summary.values(), key=lambda e: e["order"])
        return render(
            request,
            "boosters/result.html",
            {"opening": opening, "cards": ocs, "rarity_summary": rarity_summary},
        )


@method_decorator(login_required, name="dispatch")
class HistoryView(View):
    def get(self, request):
        from django.core.paginator import Paginator

        from .models import BoosterOpeningCard

        qs = (
            BoosterOpening.objects.filter(player=request.user)
            .select_related("collection", "pack")
            .order_by("-created_at")
        )
        paginator = Paginator(qs, 10)
        page = paginator.get_page(request.GET.get("page"))
        openings = list(page.object_list)

        ocs = (
            list(
                BoosterOpeningCard.objects.filter(opening__in=openings)
                .select_related("card__entity", "card__rarity", "card__collection")
                .order_by("opening_id", "position")
            )
            if openings
            else []
        )

        from inventory.models import InventoryEntry

        quantities = (
            {
                e.card_id: e.quantity
                for e in InventoryEntry.objects.filter(
                    player=request.user, card_id__in=[oc.card_id for oc in ocs]
                )
            }
            if ocs
            else {}
        )

        by_opening: dict = {}
        for oc in ocs:
            quantity = quantities.get(oc.card_id, 0)
            oc.quantity = quantity
            # Même convention que l'écran de révélation : quantité ≤ 1 = nouveauté.
            oc.is_new = quantity <= 1
            by_opening.setdefault(oc.opening_id, []).append(oc)

        rows = []
        for op in openings:
            cards = by_opening.get(op.pk, [])
            new_count = sum(1 for oc in cards if oc.is_new)
            rows.append(
                {
                    "opening": op,
                    "cards": cards,
                    "new_count": new_count,
                    "dup_count": len(cards) - new_count,
                }
            )

        from collection.models import Collection

        collection = (
            openings[0].collection
            if openings
            else Collection.objects.filter(status="active")
            .order_by("display_order", "name")
            .first()
        )

        return render(
            request,
            "boosters/history.html",
            {
                "rows": rows,
                "page_obj": page,
                "total_openings": paginator.count,
                "collection": collection,
            },
        )
