from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.request import RequestStatus


class RequestCreate(BaseModel):
    service_id: int
    title: str
    description: str


class RequestStatusUpdate(BaseModel):
    new_status: RequestStatus
    comment: str | None = None


class InternalNoteCreate(BaseModel):
    note: str


class ServiceRequestPublic(BaseModel):
    id: int
    citizen_id: int
    service_id: int
    title: str
    description: str
    current_status: RequestStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class StatusHistoryPublic(BaseModel):
    id: int
    old_status: RequestStatus
    new_status: RequestStatus
    comment: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class InternalNotePublic(BaseModel):
    id: int
    note: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestDetail(ServiceRequestPublic):
    status_history: list[StatusHistoryPublic] = []
    internal_notes: list[InternalNotePublic] = []
