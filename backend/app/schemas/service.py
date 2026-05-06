from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceCreate(BaseModel):
    code: str
    title_ar: str
    description_ar: str


class ServicePublic(BaseModel):
    id: int
    code: str
    title_ar: str
    description_ar: str
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
