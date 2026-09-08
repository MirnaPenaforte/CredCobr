from datetime import date, timedelta

from django import forms

from apps.collections.models import CollectionStatus


DATE_INPUT_FORMATS = ["%m/%d/%Y", "%Y-%m-%d"]


def date_widget(placeholder: str) -> forms.DateInput:
    return forms.DateInput(
        format="%m/%d/%Y",
        attrs={"type": "text", "placeholder": f"{placeholder} (MM/DD/AAAA)"},
    )


class CollectionUpdateForm(forms.ModelForm):
    class Meta:
        model = CollectionStatus
        fields = ["status", "notes", "expected_payment_date", "expected_amount", "next_action"]
        labels = {
            "status": "Status da cobrança",
            "notes": "Observações",
            "expected_payment_date": "Previsão de pagamento",
            "expected_amount": "Valor previsto",
            "next_action": "Próxima ação",
        }
        widgets = {
            "notes": forms.Textarea(attrs={"placeholder": "Registre as informações do contato ou da cobrança"}),
            "expected_payment_date": date_widget("Informe a data prevista"),
            "expected_amount": forms.NumberInput(attrs={"placeholder": "Informe o valor previsto"}),
            "next_action": forms.TextInput(attrs={"placeholder": "Descreva a próxima ação"}),
        }


class PaymentPromiseForm(forms.Form):
    promised_date = forms.DateField(
        label="Data da promessa",
        input_formats=DATE_INPUT_FORMATS,
        widget=date_widget("Informe a data da promessa"),
    )
    promised_amount = forms.DecimalField(
        label="Valor prometido",
        min_value=0, max_digits=14, decimal_places=2,
        widget=forms.NumberInput(attrs={"placeholder": "Informe o valor prometido"}),
    )
    notes = forms.CharField(
        label="Observações", required=False,
        widget=forms.Textarea(attrs={"placeholder": "Registre uma observação", "rows": 3}),
    )

    def clean_promised_date(self):
        promised_date = self.cleaned_data["promised_date"]
        if not date.today() <= promised_date <= date.today() + timedelta(days=7):
            raise forms.ValidationError("A promessa deve ter data entre hoje e os próximos 7 dias.")
        return promised_date


class PaymentAgreementForm(forms.Form):
    negotiated_amount = forms.DecimalField(
        label="Valor negociado",
        min_value=0, max_digits=14, decimal_places=2,
        widget=forms.NumberInput(attrs={"placeholder": "Informe o valor negociado"}),
    )
    installment_count = forms.IntegerField(
        label="Quantidade de parcelas",
        min_value=1,
        widget=forms.NumberInput(attrs={"placeholder": "Informe a quantidade de parcelas"}),
    )
    first_due_date = forms.DateField(
        label="Data do primeiro vencimento",
        input_formats=DATE_INPUT_FORMATS,
        widget=date_widget("Informe o primeiro vencimento"),
    )
    periodicity_days = forms.IntegerField(
        label="Periodicidade (dias)",
        min_value=1, initial=30,
        widget=forms.NumberInput(attrs={"placeholder": "Informe a periodicidade em dias"}),
    )
    notes = forms.CharField(
        label="Observações", required=False,
        widget=forms.Textarea(attrs={"placeholder": "Registre uma observação", "rows": 3}),
    )
