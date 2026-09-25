from __future__ import annotations

from typing import Any

from apps.customers.visibility import exclude_hidden_customers


def is_administrator(user: Any) -> bool:
    return bool(user.is_authenticated and (user.is_superuser or user.role == "administrator"))


def can_access_all_states(user: Any) -> bool:
    return bool(user.is_authenticated and user.role in {"administrator", "manager"})


def can_manage_collections(user: Any) -> bool:
    return can_access_all_states(user)


def filter_by_state_scope(queryset, user: Any, field: str = "company__state"):
    if not can_access_all_states(user):
        return queryset.none()
    relation = "customer" if queryset.model._meta.model_name == "receivable" else "receivable__customer"
    return exclude_hidden_customers(queryset, relation=relation)
