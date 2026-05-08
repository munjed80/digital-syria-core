"""Administrative scope models: Governorate, Municipality, District, Neighborhood.

These form a hierarchy used by the population registry to scope data access
per user role (governor → governorate, municipality_chief → municipality,
mukhtar → district / neighborhood).
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Governorate(Base, TimestampMixin):
    __tablename__ = "governorates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(128), nullable=False)


class Municipality(Base, TimestampMixin):
    __tablename__ = "municipalities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    governorate_id: Mapped[int] = mapped_column(
        ForeignKey("governorates.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(128), nullable=False)


class District(Base, TimestampMixin):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    municipality_id: Mapped[int] = mapped_column(
        ForeignKey("municipalities.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(128), nullable=False)


class Neighborhood(Base, TimestampMixin):
    __tablename__ = "neighborhoods"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    district_id: Mapped[int] = mapped_column(
        ForeignKey("districts.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(128), nullable=False)
