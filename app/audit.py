from __future__ import annotations

import logging

from app.db import AuditLog

logger = logging.getLogger(__name__)


def audit(
    db,
    actor: str,
    action: str,
    resource: str | None = None,
    result: str = "ok"
) -> None:
    """
    Записывает событие аудита в базу данных.

    action: "user.delete", "user.role_change", "container.create", "image.pull", ...
    result: "ok" | "denied" | "error"
    """
    try:
        db.add(AuditLog(actor=actor, action=action, resource=resource, result=result))
        db.flush()
    except Exception:
        logger.exception("audit write failed for action=%s resource=%s", action, resource)
