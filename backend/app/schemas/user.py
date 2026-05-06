from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserPublic(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True
