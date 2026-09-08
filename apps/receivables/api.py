from django.db.models import Q
from rest_framework import generics

from apps.accounts.permissions import filter_by_state_scope

from .models import Receivable
from .serializers import ReceivableSerializer


class ScopedReceivableMixin:
    def get_queryset(self):
        queryset = filter_by_state_scope(
            Receivable.objects.select_related(
                "company__state", "customer__economic_group", "operator"
            ),
            self.request.user,
        )
        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title_number__icontains=query)
                | Q(customer__name__icontains=query)
                | Q(customer__identifier__icontains=query)
            )
        for parameter, lookup in {
            "state": "company__state__code",
            "company": "company_id",
            "group": "customer__economic_group_id",
            "operator": "operator_id",
            "status": "collection_status__status",
        }.items():
            value = self.request.query_params.get(parameter)
            if value:
                queryset = queryset.filter(**{lookup: value})
        return queryset.order_by("due_date", "id")


class ReceivableListView(ScopedReceivableMixin, generics.ListAPIView):
    serializer_class = ReceivableSerializer


class ReceivableDetailView(ScopedReceivableMixin, generics.RetrieveAPIView):
    serializer_class = ReceivableSerializer
