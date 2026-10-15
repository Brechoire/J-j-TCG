from django.urls import path

from .views import CollectionDetailView, CollectionListView

app_name = "collection"

urlpatterns = [
    path("collections/", CollectionListView.as_view(), name="list"),
    path("collections/<slug:slug>/", CollectionDetailView.as_view(), name="detail"),
]
