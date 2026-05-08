from enum import Enum

from sqlalchemy import Enum as SQLEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class UserRole(str, Enum):
    # Existing roles (kept for backwards compatibility)
    citizen = "citizen"
    employee = "employee"
    supervisor = "supervisor"
    admin = "admin"
    # Population registry roles
    super_admin = "super_admin"
    governor = "governor"
    municipality_chief = "municipality_chief"
    mukhtar = "mukhtar"
    household_head = "household_head"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.citizen)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Optional administrative scope. Each role uses at most one of these
    # depending on its level (governor → governorate, municipality_chief →
    # municipality, mukhtar → district or neighborhood). Citizens and
    # household_head users typically rely on their household's scope.
    governorate_id: Mapped[int | None] = mapped_column(
        ForeignKey("governorates.id"), nullable=True, index=True
    )
    municipality_id: Mapped[int | None] = mapped_column(
        ForeignKey("municipalities.id"), nullable=True, index=True
    )
    district_id: Mapped[int | None] = mapped_column(
        ForeignKey("districts.id"), nullable=True, index=True
    )
    neighborhood_id: Mapped[int | None] = mapped_column(
        ForeignKey("neighborhoods.id"), nullable=True, index=True
    )
    national_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
