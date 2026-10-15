from django.shortcuts import get_object_or_404, render
from django.views import View

from .models import Collection


class CollectionListView(View):
    def get(self, request):
        cols = Collection.objects.filter(status="active").order_by("display_order", "name")
        return render(request, "collection/list.html", {"collections": cols})


class CollectionDetailView(View):
    def get(self, request, slug):
        col = get_object_or_404(Collection, slug=slug)
        total = col.cards.filter(is_active=True).count()
        return render(request, "collection/detail.html", {"collection": col, "total": total})
