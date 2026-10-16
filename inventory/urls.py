from django.urls import path

from .views import AlbumView, CardDetailView, InventoryListView, ResetCollectionView

app_name = "inventory"

urlpatterns = [
    path("inventaire/", InventoryListView.as_view(), name="list"),
    # TODO TEMP (dev) : route de reset à SUPPRIMER avant prod.
    path("inventaire/reinitialiser/", ResetCollectionView.as_view(), name="reset"),
    path("albums/<slug:slug>/", AlbumView.as_view(), name="album"),
    path("albums/<slug:slug>/<int:pk>/", CardDetailView.as_view(), name="card-detail"),
]
