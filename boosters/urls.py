from django.urls import path

from .views import HistoryView, OpenFreeView, ResultView

app_name = "boosters"

urlpatterns = [
    path("ouvrir/<slug:slug>/", OpenFreeView.as_view(), name="open"),
    path("<int:pk>/", ResultView.as_view(), name="result"),
    path("historique/", HistoryView.as_view(), name="history"),
]
