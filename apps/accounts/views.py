from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.audit.services import record_audit

from .forms import UserCreateForm, UserPasswordForm, UserUpdateForm
from .models import User
from .permissions import is_administrator


def administrator_required(view):
    @login_required
    def wrapped(request, *args, **kwargs):
        if not is_administrator(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped


def _user_snapshot(user):
    return {
        "username": user.username, "name": user.get_full_name(), "email": user.email,
        "whatsapp_number": user.whatsapp_number, "role": user.role, "is_active": user.is_active,
    }


@administrator_required
def user_list(request):
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "")
    status = request.GET.get("status", "")
    users = User.objects.all().order_by("username")
    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            | Q(email__icontains=query) | Q(whatsapp_number__icontains=query)
        )
    if role in dict(User.Role.choices):
        users = users.filter(role=role)
    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)
    return render(request, "accounts/user_list.html", {
        "users": users, "query": query, "selected_role": role, "selected_status": status,
        "role_choices": User.Role.choices,
    })


@administrator_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        record_audit(user=request.user, action="created", model_name="accounts.User", object_id=str(user.pk),
                     new_value=_user_snapshot(user), origin="user_management")
        messages.success(request, f"Usuário {user.username} cadastrado com sucesso.")
        return redirect("user-list")
    return render(request, "accounts/user_form.html", {"form": form, "mode": "create"})


@administrator_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=user)
    previous_value = _user_snapshot(user)
    if request.method == "POST" and form.is_valid():
        if user == request.user and not form.cleaned_data["is_active"]:
            form.add_error("is_active", "Você não pode desativar seu próprio acesso.")
        elif user == request.user and form.cleaned_data["role"] != User.Role.ADMINISTRATOR:
            form.add_error("role", "Você não pode remover seu próprio papel de administrador.")
        else:
            user = form.save()
            record_audit(user=request.user, action="updated", model_name="accounts.User", object_id=str(user.pk),
                         previous_value=previous_value, new_value=_user_snapshot(user), origin="user_management")
            messages.success(request, f"Dados de {user.username} atualizados.")
            return redirect("user-list")
    return render(request, "accounts/user_form.html", {"form": form, "managed_user": user, "mode": "update"})


@administrator_required
def user_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserPasswordForm(user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        record_audit(user=request.user, action="password_reset", model_name="accounts.User", object_id=str(user.pk),
                     origin="user_management")
        messages.success(request, f"Senha de {user.username} redefinida.")
        return redirect("user-list")
    return render(request, "accounts/user_password.html", {"form": form, "managed_user": user})


@administrator_required
@require_POST
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "Você não pode desativar seu próprio acesso.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        record_audit(user=request.user, action="activated" if user.is_active else "deactivated",
                     model_name="accounts.User", object_id=str(user.pk), new_value=_user_snapshot(user), origin="user_management")
        messages.success(request, f"Usuário {user.username} {'ativado' if user.is_active else 'desativado'}.")
    return redirect("user-list")


@administrator_required
@require_POST
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "Você não pode remover seu próprio usuário.")
    else:
        username = user.username
        previous_value = _user_snapshot(user)
        user_id = str(user.pk)
        try:
            user.delete()
        except ProtectedError:
            messages.error(request, f"O usuário {username} possui registros históricos e não pode ser removido. Desative o acesso.")
        else:
            record_audit(user=request.user, action="deleted", model_name="accounts.User", object_id=user_id,
                         previous_value=previous_value, origin="user_management")
            messages.success(request, f"Usuário {username} removido.")
    return redirect("user-list")
