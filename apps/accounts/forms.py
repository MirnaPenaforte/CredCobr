from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from apps.companies.models import State

from .models import User


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "whatsapp_number", "role", "report_states")
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "username"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "whatsapp_number": forms.TextInput(attrs={"placeholder": "+5585999999999", "inputmode": "tel"}),
        }

    report_states = forms.ModelMultipleChoiceField(
        label="Estados dos relatórios por e-mail",
        queryset=State.objects.filter(code__in=("CE", "BA", "PE")),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Os dois relatórios do estado selecionado serão enviados no mesmo e-mail.",
    )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "whatsapp_number", "role", "report_states", "is_active")
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "username"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "whatsapp_number": forms.TextInput(attrs={"placeholder": "+5585999999999", "inputmode": "tel"}),
        }

    report_states = forms.ModelMultipleChoiceField(
        label="Estados dos relatórios por e-mail",
        queryset=State.objects.filter(code__in=("CE", "BA", "PE")),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Os dois relatórios do estado selecionado serão enviados no mesmo e-mail.",
    )


class UserPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label="Nova senha", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    new_password2 = forms.CharField(label="Confirme a nova senha", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
