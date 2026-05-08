"""Pydantic schemas for administrative scope and population registry."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.population import (
    ChangeRequestStatus,
    ChangeRequestType,
    Gender,
    HouseholdVerificationStatus,
    LifeStatus,
    RelationToHead,
)


# ---------------------------------------------------------------------------
# Administrative scope
# ---------------------------------------------------------------------------


class GovernoratePublic(BaseModel):
    id: int
    code: str
    name_ar: str
    model_config = ConfigDict(from_attributes=True)


class MunicipalityPublic(BaseModel):
    id: int
    governorate_id: int
    code: str
    name_ar: str
    model_config = ConfigDict(from_attributes=True)


class DistrictPublic(BaseModel):
    id: int
    municipality_id: int
    code: str
    name_ar: str
    model_config = ConfigDict(from_attributes=True)


class NeighborhoodPublic(BaseModel):
    id: int
    district_id: int
    code: str
    name_ar: str
    model_config = ConfigDict(from_attributes=True)


class AdminScopesPublic(BaseModel):
    """Bundle of all administrative-scope reference data."""

    governorates: list[GovernoratePublic] = []
    municipalities: list[MunicipalityPublic] = []
    districts: list[DistrictPublic] = []
    neighborhoods: list[NeighborhoodPublic] = []


# ---------------------------------------------------------------------------
# Person
# ---------------------------------------------------------------------------


class PersonBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    birth_date: date | None = None
    gender: Gender
    relation_to_head: RelationToHead = RelationToHead.other
    national_id: str | None = Field(default=None, max_length=64)
    digital_identity_ref: str | None = Field(default=None, max_length=128)


class PersonCreate(PersonBase):
    household_id: int


class PersonPublic(PersonBase):
    id: int
    household_id: int
    life_status: LifeStatus
    death_date: date | None = None
    is_archived: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Household
# ---------------------------------------------------------------------------


class HouseholdBase(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    address_line: str = Field(min_length=1, max_length=255)
    governorate_id: int
    municipality_id: int
    district_id: int
    neighborhood_id: int | None = None
    assigned_mukhtar_user_id: int | None = None
    head_user_id: int | None = None


class HouseholdCreate(HouseholdBase):
    pass


class HouseholdUpdate(BaseModel):
    address_line: str | None = Field(default=None, max_length=255)
    governorate_id: int | None = None
    municipality_id: int | None = None
    district_id: int | None = None
    neighborhood_id: int | None = None
    assigned_mukhtar_user_id: int | None = None
    verification_status: HouseholdVerificationStatus | None = None


class HouseholdPublic(HouseholdBase):
    id: int
    head_person_id: int | None = None
    verification_status: HouseholdVerificationStatus
    is_archived: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class HouseholdDetail(HouseholdPublic):
    members: list[PersonPublic] = []


# ---------------------------------------------------------------------------
# Change requests
# ---------------------------------------------------------------------------


class ChangeRequestCreate(BaseModel):
    request_type: ChangeRequestType
    household_id: int
    target_person_id: int | None = None
    # Phase-2 alias — accept either name on input.
    person_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None

    def resolved_person_id(self) -> int | None:
        return self.person_id if self.person_id is not None else self.target_person_id


class ChangeRequestDecision(BaseModel):
    approve: bool
    comment: str | None = None


class ChangeRequestPublic(BaseModel):
    id: int
    request_number: str | None = None
    request_type: ChangeRequestType
    status: ChangeRequestStatus
    submitted_by_user_id: int
    household_id: int
    target_person_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None
    # Unified Phase-2 review/approve fields.
    reviewed_by_user_id: int | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    approved_by_user_id: int | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    # Legacy review fields (kept for backwards compatibility with the
    # Phase-1 mukhtar/municipality two-step workflow).
    mukhtar_user_id: int | None = None
    mukhtar_decision_at: datetime | None = None
    mukhtar_comment: str | None = None
    municipality_user_id: int | None = None
    municipality_decision_at: datetime | None = None
    municipality_comment: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Phase-2 unified change-request schemas
# ---------------------------------------------------------------------------


class PopulationChangeRequestCreate(BaseModel):
    """Payload accepted by `POST /population/change-requests`."""

    request_type: ChangeRequestType
    household_id: int
    person_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None


class PopulationChangeRequestUpdate(BaseModel):
    """Allowed mutations on a non-finalised request by its owner."""

    payload: dict[str, Any] | None = None
    reason: str | None = None


class PopulationChangeRequestReview(BaseModel):
    """Reviewer action — `under_review`, `rejected`, or `approved`.

    `action` controls the resulting status:
        * `start`     → status = under_review
        * `approve`   → status = approved (applies the change)
        * `reject`    → status = rejected (requires `rejection_reason`)
    """

    action: str = Field(pattern=r"^(start|approve|reject)$")
    review_notes: str | None = None
    rejection_reason: str | None = None


class PopulationChangeRequestApprove(BaseModel):
    """Final approval payload for `POST /change-requests/{id}/approve`."""

    review_notes: str | None = None


class PopulationChangeRequestRead(ChangeRequestPublic):
    """Alias for the Phase-2 spec naming — same shape as ChangeRequestPublic."""

    pass


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


class AgeGroupBreakdown(BaseModel):
    label: str
    count: int


class GenderBreakdown(BaseModel):
    male: int = 0
    female: int = 0


class StatusBreakdown(BaseModel):
    label: str
    count: int


class AdministrativeBreakdownItem(BaseModel):
    id: int
    name_ar: str
    households: int
    population: int


class PopulationStatistics(BaseModel):
    scope_label: str
    total_population: int
    total_households: int
    verified_households: int
    pending_households: int
    births_last_year: int
    deaths_last_year: int
    age_groups: list[AgeGroupBreakdown]
    gender: GenderBreakdown
    requests_by_status: list[StatusBreakdown]
    administrative_breakdown: list[AdministrativeBreakdownItem] = []
