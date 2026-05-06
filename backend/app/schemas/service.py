from pydantic import BaseModel


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

    class Config:
        from_attributes = True
