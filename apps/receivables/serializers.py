from datetime import date

from rest_framework import serializers

from apps.processing.services import calculate_receivable_overdue_days, classify_overdue_days

from .models import Receivable


class ReceivableSerializer(serializers.ModelSerializer):
    issued_at = serializers.DateField(format="%m/%d/%Y", read_only=True, allow_null=True)
    due_date = serializers.DateField(format="%m/%d/%Y", read_only=True)
    company = serializers.CharField(source="company.name", read_only=True)
    state = serializers.CharField(source="company.state.code", read_only=True)
    customer = serializers.CharField(source="customer.name", read_only=True)
    customer_identifier = serializers.CharField(source="customer.identifier", read_only=True)
    group = serializers.CharField(source="customer.economic_group.name", read_only=True, default="")
    operator = serializers.CharField(source="operator.username", read_only=True, default="")
    overdue_days = serializers.SerializerMethodField()
    overdue_band = serializers.SerializerMethodField()

    class Meta:
        model = Receivable
        fields = [
            "id", "title_number", "installment", "customer_identifier", "customer", "group",
            "company", "state", "original_amount", "interest_amount", "penalty_amount",
            "outstanding_amount", "term_days", "interest_rate", "daily_interest_amount",
            "balance_with_interest", "issued_at", "due_date", "overdue_days", "overdue_band",
            "source_status", "seller", "agent_code", "origin_establishment_code", "establishment_code",
            "financial_status", "operator", "created_at", "updated_at",
        ]

    def get_overdue_days(self, obj):
        return calculate_receivable_overdue_days(obj, date.today())

    def get_overdue_band(self, obj):
        return classify_overdue_days(self.get_overdue_days(obj)).value
