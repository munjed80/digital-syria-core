from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_audit_log(
    db: Session,
    *,
    actor_user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            log_metadata=metadata,
            created_at=now_iso(),
        )
    )
