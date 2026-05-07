from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationPublic

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationPublic])
def list_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Notification]:
    """Return notifications belonging to the authenticated user only.

    Every authenticated role (citizen, employee, supervisor, admin) only ever
    sees their own notifications. Cross-user reads are not supported.
    """
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(Notification.id.desc())
        )
    )


@router.patch("/{notification_id}/read", response_model=NotificationPublic)
def mark_notification_read(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Notification:
    """Mark a notification as read.

    A user may only mark their own notifications as read. Attempting to mark
    another user's notification returns 404 (not 403) to avoid leaking the
    existence of notifications belonging to other users.
    """
    notification = db.scalar(
        select(Notification).where(Notification.id == notification_id)
    )
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")

    if not notification.is_read:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
    return notification
