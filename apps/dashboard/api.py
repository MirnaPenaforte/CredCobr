from datetime import date

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import filter_by_state_scope
from apps.processing.services import calculate_indicators, top_general_customers, top_groups
from apps.receivables.models import Receivable


class DashboardSummaryView(APIView):
    def get(self, request):
        receivables = filter_by_state_scope(Receivable.objects.select_related("company__state", "customer__economic_group"), request.user)
        indicators = calculate_indicators(receivables, date.today())
        return Response({key: str(value) if hasattr(value, "as_tuple") else value for key, value in indicators.items()})


class DashboardTopGroupsView(APIView):
    def get(self, request):
        receivables = filter_by_state_scope(
            Receivable.objects.select_related("customer__economic_group").prefetch_related("payment_promises", "agreements__installments"), request.user
        )
        return Response([{**item, "amount": str(item["amount"])} for item in top_groups(receivables)])


class DashboardTopCustomersView(APIView):
    def get(self, request):
        receivables = filter_by_state_scope(
            Receivable.objects.select_related("customer__economic_group").prefetch_related("payment_promises", "agreements__installments"), request.user
        )
        return Response([{**item, "amount": str(item["amount"])} for item in top_general_customers(receivables)])
