from __future__ import annotations

from typing import Any


def is_administrator(user: Any) -> bool:
    return bool(user.is_authenticated and (user.is_superuser or user.role == "administrator"))


def can_access_all_states(user: Any) -> bool:
    return bool(user.is_authenticated and user.role in {"administrator", "manager"})


def can_manage_collections(user: Any) -> bool:
    return can_access_all_states(user)


def filter_by_state_scope(queryset, user: Any, field: str = "company__state"):
    return queryset if can_access_all_states(user) else queryset.none()
