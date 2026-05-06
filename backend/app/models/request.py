from enum import Enum

from sqlalchemy import Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class RequestStatus(str, Enum):
    submitted = "submitted"
    under_review = "under_review"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"


class ServiceRequest(Base, TimestampMixin):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("service_catalog.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    current_status: Mapped[RequestStatus] = mapped_column(SQLEnum(RequestStatus), default=RequestStatus.submitted, nullable=False)


class RequestStatusHistory(Base, TimestampMixin):
    __tablename__ = "request_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_requests.id"), nullable=False, index=True)
    changed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    old_status: Mapped[RequestStatus] = mapped_column(SQLEnum(RequestStatus), nullable=False)
    new_status: Mapped[RequestStatus] = mapped_column(SQLEnum(RequestStatus), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class InternalNote(Base, TimestampMixin):
    __tablename__ = "internal_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_requests.id"), nullable=False, index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
