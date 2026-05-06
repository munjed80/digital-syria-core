from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.service import ServiceCatalogItem
from app.models.user import User, UserRole
from app.schemas.service import ServiceCreate, ServicePublic
from app.services.audit import write_audit_log

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServicePublic])
def list_services(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[ServiceCatalogItem]:
    return list(db.scalars(select(ServiceCatalogItem).where(ServiceCatalogItem.is_active.is_(True))))


@router.post("", response_model=ServicePublic, status_code=201)
def create_service(
    payload: ServiceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.admin))],
) -> ServiceCatalogItem:
    item = ServiceCatalogItem(
        code=payload.code,
        title_ar=payload.title_ar,
        description_ar=payload.description_ar,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="service.create",
        entity_type="service",
        entity_id=str(item.id),
        metadata={"code": item.code},
    )
    db.commit()
    db.refresh(item)
    return item
