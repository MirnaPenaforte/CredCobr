from __future__ import annotations

from typing import Any

from .models import AuditLog


def record_audit(
    *,
    user: Any,
    action: str,
    model_name: str,
    object_id: str,
    previous_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    origin: str,
    reason: str = "",
) -> AuditLog:
    return AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        previous_value=previous_value,
        new_value=new_value,
        origin=origin,
        reason=reason,
    )
