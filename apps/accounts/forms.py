from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm

from .models import User


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "whatsapp_number", "role")
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "username"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "whatsapp_number": forms.TextInput(attrs={"placeholder": "+5585999999999", "inputmode": "tel"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "whatsapp_number", "role", "is_active")
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "username"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "whatsapp_number": forms.TextInput(attrs={"placeholder": "+5585999999999", "inputmode": "tel"}),
        }


class UserPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label="Nova senha", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    new_password2 = forms.CharField(label="Confirme a nova senha", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
