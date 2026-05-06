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

    model_config = ConfigDict(from_attributes=True)
