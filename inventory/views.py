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
        from collection.packs import packs_for_card

        packs = packs_for_card(card, list(col.packs.filter(is_active=True)))
        return render(
            request,
            "inventory/card_detail.html",
            {
                "collection": col,
                "card": card,
                "quantity": entry.quantity if entry else 0,
                "packs": packs,
            },
        )


@method_decorator(login_required, name="dispatch")
class InventoryListView(View):
    allowed_sorts = ("recent", "rarity_desc", "rarity_asc", "name")
    # Abréviations compactes des pastilles (style TCG : C · PC · R · E · L).
    rarity_abbr = {
        "common": "C",
        "uncommon": "PC",
        "rare": "R",
        "epic": "E",
        "legendary": "L",
    }

    def get(self, request):
        from urllib.parse import urlencode

        from django.db.models import Count, F

        from cards.models import Rarity
        from inventory.models import InventoryEntry

        sort = request.GET.get("sort", "recent")
        if sort not in self.allowed_sorts:
            sort = "recent"
        doubles = request.GET.get("doubles") == "1"

        rarities = list(Rarity.objects.filter(is_active=True).order_by("order"))
        valid_codes = {r.code for r in rarities}
        rarity = request.GET.get("rarity", "")
        if rarity not in valid_codes:
            rarity = ""

        qs = InventoryEntry.objects.filter(player=request.user).select_related(
            "card__collection", "card__entity", "card__rarity"
        )
        if doubles:
            qs = qs.filter(quantity__gte=2)
        if rarity:
            qs = qs.filter(card__rarity__code=rarity)
        if sort == "name":
            qs = qs.order_by("card__entity__label_fr", "-last_obtained_at")
        elif sort == "rarity_desc":
            qs = qs.order_by(
                F("card__rarity__order").desc(nulls_last=True),
                "card__entity__label_fr",
            )
        elif sort == "rarity_asc":
            qs = qs.order_by(
                F("card__rarity__order").asc(nulls_last=True),
                "card__entity__label_fr",
            )
        else:
            qs = qs.order_by("-last_obtained_at")
        entries = list(qs)

        scoped = InventoryEntry.objects.filter(player=request.user)
        if doubles:
            scoped = scoped.filter(quantity__gte=2)
        counts = dict(
            scoped.values("card__rarity__code")
            .annotate(n=Count("id"))
            .values_list("card__rarity__code", "n")
        )
        total_count = sum(counts.values())
        has_any = InventoryEntry.objects.filter(player=request.user).exists()
        doubles_count = InventoryEntry.objects.filter(player=request.user, quantity__gte=2).count()
        # Params à conserver dans les liens (tri + filtre doublons).
        keep = {}
        if sort != "recent":
            keep["sort"] = sort
        if doubles:
            keep["doubles"] = "1"
        keep_qs = urlencode(keep)
        chips = [
            {
                "code": r.code,
                "name": r.name,
                "abbr": self.rarity_abbr.get(r.code, r.code[:2].upper()),
                "count": counts.get(r.code, 0),
            }
            for r in rarities
        ]

        from collection.models import Collection

        collection = (
            Collection.objects.filter(status="active").order_by("display_order", "name").first()
        )
        return render(
            request,
            "inventory/list.html",
            {
                "entries": entries,
                "sort": sort,
                "rarity": rarity,
                "chips": chips,
                "total_count": total_count,
                "has_any": has_any,
                "doubles": doubles,
                "doubles_count": doubles_count,
                "keep_qs": keep_qs,
                "collection": collection,
            },
        )


# TODO TEMP (dev) : vue de reset total à SUPPRIMER avant prod (avec son URL,
# son bouton profil et ses tests). Sert aux essais : vide tout côté joueur.
@method_decorator(login_required, name="dispatch")
class ResetCollectionView(View):
    def post(self, request):
        from django.shortcuts import redirect

        from accounts.models import PlayerProfile
        from boosters.models import BoosterOpening
        from inventory.models import InventoryEntry

        BoosterOpening.objects.filter(player=request.user).delete()
        InventoryEntry.objects.filter(player=request.user).delete()
        PlayerProfile.objects.filter(user=request.user).update(
            last_free_opened_at=None, total_opened=0, unique_discovered=0
        )
        return redirect("accounts:profile")

    def get(self, request):
        from django.http import HttpResponseNotAllowed

        return HttpResponseNotAllowed(["POST"])
