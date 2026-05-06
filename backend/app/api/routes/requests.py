from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.notification import Notification
from app.models.request import InternalNote, RequestStatus, RequestStatusHistory, ServiceRequest
from app.models.service import ServiceCatalogItem
from app.models.user import User, UserRole
from app.schemas.request import InternalNoteCreate, RequestCreate, RequestStatusUpdate, ServiceRequestPublic
from app.services.audit import write_audit_log

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", response_model=ServiceRequestPublic, status_code=201)
def create_request(
    payload: RequestCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.citizen))],
) -> ServiceRequest:
    service = db.scalar(select(ServiceCatalogItem).where(ServiceCatalogItem.id == payload.service_id))
    if service is None or not service.is_active:
        raise HTTPException(status_code=404, detail="Service not found")

    request_record = ServiceRequest(
        citizen_id=current_user.id,
        service_id=payload.service_id,
        title=payload.title,
        description=payload.description,
        current_status=RequestStatus.submitted,
    )
    db.add(request_record)
    db.flush()
    db.add(
        RequestStatusHistory(
            request_id=request_record.id,
            changed_by_user_id=current_user.id,
            old_status=RequestStatus.submitted,
            new_status=RequestStatus.submitted,
            comment="Initial submission",
        )
    )
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="request.create",
        entity_type="service_request",
        entity_id=str(request_record.id),
        metadata={"service_id": payload.service_id},
    )
    db.commit()
    db.refresh(request_record)
    return request_record


@router.get("", response_model=list[ServiceRequestPublic])
def list_requests(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ServiceRequest]:
    query = select(ServiceRequest)
    if current_user.role == UserRole.citizen:
        query = query.where(ServiceRequest.citizen_id == current_user.id)
    return list(db.scalars(query.order_by(ServiceRequest.id.desc())))


@router.patch("/{request_id}/status", response_model=ServiceRequestPublic)
def update_status(
    request_id: int,
    payload: RequestStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.employee, UserRole.supervisor, UserRole.admin))],
) -> ServiceRequest:
    request_record = db.scalar(select(ServiceRequest).where(ServiceRequest.id == request_id))
    if request_record is None:
        raise HTTPException(status_code=404, detail="Request not found")

    old_status = request_record.current_status
    request_record.current_status = payload.new_status
    db.add(
        RequestStatusHistory(
            request_id=request_record.id,
            changed_by_user_id=current_user.id,
            old_status=old_status,
            new_status=payload.new_status,
            comment=payload.comment,
        )
    )
    db.add(
        Notification(
            user_id=request_record.citizen_id,
            message=f"تم تحديث حالة الطلب رقم {request_record.id} إلى {payload.new_status.value}",
        )
    )
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="request.status_update",
        entity_type="service_request",
        entity_id=str(request_record.id),
        metadata={"old_status": old_status.value, "new_status": payload.new_status.value},
    )
    db.commit()
    db.refresh(request_record)
    return request_record


@router.post("/{request_id}/notes", status_code=201)
def add_internal_note(
    request_id: int,
    payload: InternalNoteCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.employee, UserRole.supervisor, UserRole.admin))],
) -> dict[str, str]:
    request_record = db.scalar(select(ServiceRequest).where(ServiceRequest.id == request_id))
    if request_record is None:
        raise HTTPException(status_code=404, detail="Request not found")

    db.add(InternalNote(request_id=request_id, author_user_id=current_user.id, note=payload.note))
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="request.note_add",
        entity_type="service_request",
        entity_id=str(request_id),
        metadata={"note_length": len(payload.note)},
    )
    db.commit()
    return {"status": "created"}
