import uuid

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from collection.models import Collection

from .models import BoosterOpening
from .services import BoosterOpeningService, CooldownNotReady


@method_decorator(login_required, name="dispatch")
class OpenFreeView(View):
    def post(self, request, slug):
        col = get_object_or_404(Collection, slug=slug)
        try:
            opening = BoosterOpeningService().open_free(
                request.user, col, idempotency_key=uuid.uuid4()
            )
        except CooldownNotReady as e:
            return render(
                request,
                "boosters/cooldown.html",
                {"next_available": e.next_available, "collection": col},
                status=429,
            )
        return redirect("boosters:result", pk=opening.pk)


@method_decorator(login_required, name="dispatch")
class ResultView(View):
    def get(self, request, pk):
        opening = get_object_or_404(BoosterOpening, pk=pk, player=request.user)
        cards = opening.opening_cards.select_related("card__entity", "card__rarity")
        return render(request, "boosters/result.html", {"opening": opening, "cards": cards})


@method_decorator(login_required, name="dispatch")
class HistoryView(View):
    def get(self, request):
        openings = BoosterOpening.objects.filter(player=request.user).select_related("collection")[
            :50
        ]
        return render(request, "boosters/history.html", {"openings": openings})
