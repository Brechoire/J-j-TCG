from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View

from cards.models import Card
from collection.models import Collection

from .services import get_album_data


@method_decorator(login_required, name="dispatch")
class AlbumView(View):
    def get(self, request, slug):
        col = get_object_or_404(Collection, slug=slug)
        data = get_album_data(
            request.user,
            col,
            rarity_code=request.GET.get("rarity") or None,
            q=request.GET.get("q") or None,
            box=request.GET.get("box") or "all",
        )
        return render(request, "inventory/album.html", {"collection": col, "data": data})


@method_decorator(login_required, name="dispatch")
class CardDetailView(View):
    def get(self, request, slug, pk):
        col = get_object_or_404(Collection, slug=slug)
        card = get_object_or_404(Card, pk=pk, collection=col)
        from inventory.models import InventoryEntry

        entry = InventoryEntry.objects.filter(player=request.user, card=card).first()
        return render(
            request,
            "inventory/card_detail.html",
            {"collection": col, "card": card, "quantity": entry.quantity if entry else 0},
        )


@method_decorator(login_required, name="dispatch")
class InventoryListView(View):
    def get(self, request):
        from inventory.models import InventoryEntry

        entries = (
            InventoryEntry.objects.filter(player=request.user)
            .select_related("card__collection", "card__entity", "card__rarity")
            .order_by("-last_obtained_at")
        )
        return render(request, "inventory/list.html", {"entries": entries})
