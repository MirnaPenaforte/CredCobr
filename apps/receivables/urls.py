from django.urls import path

from .api import ReceivableDetailView, ReceivableListView


urlpatterns = [
    path("", ReceivableListView.as_view(), name="api-receivable-list"),
    path("<int:pk>/", ReceivableDetailView.as_view(), name="api-receivable-detail"),
]
