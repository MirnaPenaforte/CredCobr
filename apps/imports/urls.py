from django.urls import path

from .api import ImportBatchDetailView, ImportBatchListCreateView


urlpatterns = [
    path("", ImportBatchListCreateView.as_view(), name="api-import-list-create"),
    path("<int:pk>/", ImportBatchDetailView.as_view(), name="api-import-detail"),
]
