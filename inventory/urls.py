from django.urls import path

from .views import AlbumView, CardDetailView, InventoryListView

app_name = "inventory"

urlpatterns = [
    path("inventaire/", InventoryListView.as_view(), name="list"),
    path("albums/<slug:slug>/", AlbumView.as_view(), name="album"),
    path("albums/<slug:slug>/<int:pk>/", CardDetailView.as_view(), name="card-detail"),
]
