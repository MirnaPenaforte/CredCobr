from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response

from apps.accounts.api_permissions import CollectionWritePermission
from apps.accounts.permissions import filter_by_state_scope
from apps.receivables.models import Receivable

from .models import CollectionStatus
from .serializers import CollectionInteractionSerializer, CollectionStatusSerializer, PaymentAgreementSerializer, PaymentPromiseSerializer
from .services import create_agreement, register_interaction, register_payment_promise, update_status


def scoped_receivable(request, pk):
    return get_object_or_404(filter_by_state_scope(Receivable.objects.all(), request.user), pk=pk)


class CollectionListView(generics.ListAPIView):
    serializer_class = CollectionStatusSerializer

    def get_queryset(self):
        return filter_by_state_scope(CollectionStatus.objects.select_related("receivable"), self.request.user)


class CollectionDetailView(generics.RetrieveAPIView):
    serializer_class = CollectionStatusSerializer

    def get_queryset(self):
        return filter_by_state_scope(CollectionStatus.objects.select_related("receivable"), self.request.user)


class CollectionStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [CollectionWritePermission]
    serializer_class = CollectionStatusSerializer
    http_method_names = ["patch"]

    def get_object(self):
        receivable = scoped_receivable(self.request, self.kwargs["pk"])
        collection, _ = CollectionStatus.objects.get_or_create(receivable=receivable)
        return collection

    def perform_update(self, serializer):
        collection = self.get_object()
        update_status(collection, user=self.request.user, **serializer.validated_data)


class InteractionCreateView(generics.CreateAPIView):
    permission_classes = [CollectionWritePermission]
    serializer_class = CollectionInteractionSerializer

    def create(self, request, *args, **kwargs):
        receivable = scoped_receivable(request, kwargs["pk"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interaction = register_interaction(receivable=receivable, user=request.user, **serializer.validated_data)
        return Response(self.get_serializer(interaction).data, status=status.HTTP_201_CREATED)


class PromiseCreateView(generics.CreateAPIView):
    permission_classes = [CollectionWritePermission]
    serializer_class = PaymentPromiseSerializer

    def create(self, request, *args, **kwargs):
        receivable = scoped_receivable(request, kwargs["pk"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        promise = register_payment_promise(receivable=receivable, user=request.user, **serializer.validated_data)
        return Response(self.get_serializer(promise).data, status=status.HTTP_201_CREATED)


class AgreementCreateView(generics.CreateAPIView):
    permission_classes = [CollectionWritePermission]
    serializer_class = PaymentAgreementSerializer

    def create(self, request, *args, **kwargs):
        receivable = scoped_receivable(request, kwargs["pk"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        agreement = create_agreement(
            receivable=receivable,
            user=request.user,
            negotiated_amount=data["negotiated_amount"],
            installment_count=data["installment_count"],
            first_due_date=data.get("first_due_date", date.today()),
            periodicity_days=data.get("periodicity_days", 30),
        )
        return Response(self.get_serializer(agreement).data, status=status.HTTP_201_CREATED)
