from rest_framework import serializers

from .models import AgreementInstallment, CollectionInteraction, CollectionStatus, PaymentAgreement, PaymentPromise


class CollectionStatusSerializer(serializers.ModelSerializer):
    expected_payment_date = serializers.DateField(
        format="%m/%d/%Y", input_formats=["%m/%d/%Y", "iso-8601"], required=False, allow_null=True
    )

    class Meta:
        model = CollectionStatus
        fields = ["id", "receivable", "status", "notes", "expected_payment_date", "expected_amount", "next_action", "updated_by", "updated_at"]
        read_only_fields = ["id", "updated_by", "updated_at"]


class CollectionInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionInteraction
        fields = ["id", "channel", "notes", "next_action", "created_at"]
        read_only_fields = ["id", "created_at"]


class PaymentPromiseSerializer(serializers.ModelSerializer):
    promised_date = serializers.DateField(format="%m/%d/%Y", input_formats=["%m/%d/%Y", "iso-8601"])

    class Meta:
        model = PaymentPromise
        fields = ["id", "promised_date", "promised_amount", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]


class AgreementInstallmentSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(format="%m/%d/%Y", read_only=True)
    paid_at = serializers.DateField(format="%m/%d/%Y", read_only=True, allow_null=True)

    class Meta:
        model = AgreementInstallment
        fields = ["number", "due_date", "amount", "paid_at"]


class PaymentAgreementSerializer(serializers.ModelSerializer):
    installments = AgreementInstallmentSerializer(many=True, read_only=True)
    first_due_date = serializers.DateField(
        write_only=True, required=False, input_formats=["%m/%d/%Y", "iso-8601"]
    )

    class Meta:
        model = PaymentAgreement
        fields = ["id", "negotiated_amount", "installment_count", "periodicity_days", "status", "first_due_date", "installments", "created_at"]
        read_only_fields = ["id", "status", "installments", "created_at"]
