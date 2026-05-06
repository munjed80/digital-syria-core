from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.request import RequestStatus, ServiceRequest
from app.models.user import User, UserRole

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.employee, UserRole.supervisor, UserRole.admin))],
) -> dict[str, int]:
    total = db.scalar(select(func.count(ServiceRequest.id))) or 0
    submitted = db.scalar(select(func.count(ServiceRequest.id)).where(ServiceRequest.current_status == RequestStatus.submitted)) or 0
    in_progress = db.scalar(select(func.count(ServiceRequest.id)).where(ServiceRequest.current_status == RequestStatus.in_progress)) or 0
    resolved = db.scalar(select(func.count(ServiceRequest.id)).where(ServiceRequest.current_status == RequestStatus.resolved)) or 0
    return {
        "total_requests": int(total),
        "submitted_requests": int(submitted),
        "in_progress_requests": int(in_progress),
        "resolved_requests": int(resolved),
    }
