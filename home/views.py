from django.utils import timezone
from django.views.generic import TemplateView

from core import constants


def cooldown_label(seconds=constants.FREE_BOOSTER_COOLDOWN_SECONDS) -> str:
    if seconds % 60 == 0:
        minutes = seconds // 60
        return "1 minute" if minutes == 1 else f"{minutes} minutes"
    return "1 seconde" if seconds == 1 else f"{seconds} secondes"


class HomeView(TemplateView):
    template_name = "home/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from collection.models import Collection

        collections = list(
            Collection.objects.filter(status="active").order_by("display_order", "name")
        )
        col = collections[0] if collections else None
        ctx["collections"] = collections
        ctx["collection"] = col
        ctx["cooldown_label"] = cooldown_label()

        user = self.request.user
        ctx["album"] = None
        ctx["recent_openings"] = []
        ctx["booster_ready"] = False
        ctx["next_available"] = None
        if user.is_authenticated and col is not None:
            from accounts.models import PlayerProfile

            profile = PlayerProfile.objects.filter(user=user).first()
            now = timezone.now()
            last = profile.last_free_opened_at if profile else None
            if last is None:
                ctx["booster_ready"] = True
            else:
                elapsed = (now - last).total_seconds()
                if elapsed >= constants.FREE_BOOSTER_COOLDOWN_SECONDS:
                    ctx["booster_ready"] = True
                else:
                    ctx["next_available"] = last + timezone.timedelta(
                        seconds=constants.FREE_BOOSTER_COOLDOWN_SECONDS
                    )
            from inventory.services import get_album_data

            ctx["album"] = get_album_data(user, col)

            from boosters.models import BoosterOpening

            openings = (
                BoosterOpening.objects.filter(player=user)
                .order_by("-created_at")[:3]
                .prefetch_related("opening_cards__card__rarity")
            )
            recent = []
            for op in openings:
                rarities = [
                    (oc.card.rarity.code, oc.card.rarity.name)
                    for oc in op.opening_cards.all()
                    if oc.card.rarity_id
                ]
                recent.append(
                    {
                        "opening": op,
                        "rarities": rarities,
                        "names": ", ".join(name for _, name in rarities),
                    }
                )
            ctx["recent_openings"] = recent
        return ctx
