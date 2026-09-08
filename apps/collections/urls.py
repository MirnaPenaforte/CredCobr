from django.urls import path

from .api import AgreementCreateView, CollectionDetailView, CollectionListView, CollectionStatusUpdateView, InteractionCreateView, PromiseCreateView


urlpatterns = [
    path("", CollectionListView.as_view()),
    path("<int:pk>/", CollectionDetailView.as_view()),
    path("<int:pk>/status/", CollectionStatusUpdateView.as_view()),
    path("<int:pk>/interactions/", InteractionCreateView.as_view()),
    path("<int:pk>/payment-promises/", PromiseCreateView.as_view()),
    path("<int:pk>/agreements/", AgreementCreateView.as_view()),
]
