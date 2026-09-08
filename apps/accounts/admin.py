from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "email", "whatsapp_number", "role", "is_active"]
    list_filter = ["role", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email", "whatsapp_number"]
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Perfil do CRED-COBR", {"fields": ("role", "whatsapp_number")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "Perfil do CRED-COBR",
            {"fields": ("email", "first_name", "last_name", "whatsapp_number", "role")},
        ),
    )

    @staticmethod
    def _is_administrator(request) -> bool:
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == User.Role.ADMINISTRATOR
        )

    def has_module_permission(self, request):
        return self._is_administrator(request)

    def has_view_permission(self, request, obj=None):
        return self._is_administrator(request)

    def has_add_permission(self, request):
        return self._is_administrator(request)

    def has_change_permission(self, request, obj=None):
        return self._is_administrator(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_administrator(request)
