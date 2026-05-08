"""Population registry models: Household, Person, change requests, event log."""

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Gender(str, Enum):
    male = "male"
    female = "female"


class LifeStatus(str, Enum):
    alive = "alive"
    deceased = "deceased"


class HouseholdVerificationStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class RelationToHead(str, Enum):
    self = "self"
    spouse = "spouse"
    child = "child"
    parent = "parent"
    sibling = "sibling"
    other = "other"


class ChangeRequestType(str, Enum):
    birth = "birth"
    death = "death"
    address_change = "address_change"
    correction = "correction"
    add_member = "add_member"
    remove_member = "remove_member"


class ChangeRequestStatus(str, Enum):
    submitted = "submitted"
    mukhtar_review = "mukhtar_review"
    municipality_review = "municipality_review"
    approved = "approved"
    rejected = "rejected"


class Household(Base, TimestampMixin):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)

    # Head of household — references a Person record.
    head_person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id", use_alter=True, name="fk_household_head_person"),
        nullable=True,
    )
    # The user account that manages this household (a `household_head` role
    # user). Optional — a household may exist without a registered citizen
    # account yet.
    head_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    address_line: Mapped[str] = mapped_column(String(255), nullable=False)
    governorate_id: Mapped[int] = mapped_column(
        ForeignKey("governorates.id"), nullable=False, index=True
    )
    municipality_id: Mapped[int] = mapped_column(
        ForeignKey("municipalities.id"), nullable=False, index=True
    )
    district_id: Mapped[int] = mapped_column(
        ForeignKey("districts.id"), nullable=False, index=True
    )
    neighborhood_id: Mapped[int | None] = mapped_column(
        ForeignKey("neighborhoods.id"), nullable=True, index=True
    )

    assigned_mukhtar_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    verification_status: Mapped[HouseholdVerificationStatus] = mapped_column(
        SQLEnum(HouseholdVerificationStatus),
        default=HouseholdVerificationStatus.pending,
        nullable=False,
        index=True,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Person(Base, TimestampMixin):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[Gender] = mapped_column(SQLEnum(Gender), nullable=False)
    relation_to_head: Mapped[RelationToHead] = mapped_column(
        SQLEnum(RelationToHead), nullable=False, default=RelationToHead.other
    )
    life_status: Mapped[LifeStatus] = mapped_column(
        SQLEnum(LifeStatus), nullable=False, default=LifeStatus.alive, index=True
    )
    death_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Reference to national / digital identity (not a hard FK — issued by
    # external civil registry systems).
    national_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    digital_identity_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)

    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)


class PopulationChangeRequest(Base, TimestampMixin):
    __tablename__ = "population_change_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    request_type: Mapped[ChangeRequestType] = mapped_column(
        SQLEnum(ChangeRequestType), nullable=False, index=True
    )
    status: Mapped[ChangeRequestStatus] = mapped_column(
        SQLEnum(ChangeRequestStatus),
        nullable=False,
        default=ChangeRequestStatus.submitted,
        index=True,
    )
    submitted_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id"), nullable=False, index=True
    )
    target_person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )

    # Free-form structured payload describing the requested change. Schema
    # depends on `request_type`. Validated at the API layer.
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    mukhtar_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    mukhtar_decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    mukhtar_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    municipality_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    municipality_decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    municipality_comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class PopulationEventLog(Base):
    """Append-only log of every mutation performed on the population registry.

    This is in addition to the generic `audit_logs` table — it is purpose-built
    for population-related history (births, deaths, address changes, etc.) so
    that statistics and citizen-facing family timelines can be produced
    efficiently without scanning the global audit log.
    """

    __tablename__ = "population_event_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    household_id: Mapped[int | None] = mapped_column(
        ForeignKey("households.id"), nullable=True, index=True
    )
    person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )
    change_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("population_change_requests.id"), nullable=True, index=True
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
