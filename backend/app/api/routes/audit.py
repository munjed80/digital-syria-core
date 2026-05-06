from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogPublic

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogPublic])
def list_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.admin))],
) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(200)))
