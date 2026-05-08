"""Population registry API.

Endpoints under `/api/v1/population/*`.

Citizens / household_head users MUST NOT mutate official person records
directly — they must submit a `PopulationChangeRequest` which is reviewed by
the assigned mukhtar (and, for higher-risk changes, also by the municipality
chief) before the registry is updated. All mutations are audited via both
the generic audit log and the population event log.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.admin_scope import Governorate, Municipality
from app.models.notification import Notification
from app.models.population import (
    ChangeRequestStatus,
    ChangeRequestType,
    Gender,
    Household,
    HouseholdVerificationStatus,
    LifeStatus,
    Person,
    PopulationChangeRequest,
    PopulationEventLog,
    RelationToHead,
)
from app.models.user import User, UserRole
from app.schemas.population import (
    AdministrativeBreakdownItem,
    AgeGroupBreakdown,
    ChangeRequestCreate,
    ChangeRequestDecision,
    ChangeRequestPublic,
    GenderBreakdown,
    HouseholdCreate,
    HouseholdDetail,
    HouseholdPublic,
    HouseholdUpdate,
    PersonCreate,
    PersonPublic,
    PopulationStatistics,
    StatusBreakdown,
)
from app.services.audit import write_audit_log
from app.services.population_rbac import (
    DIRECT_REGISTRY_WRITE_ROLES,
    HIGH_RISK_CHANGE_TYPES,
    POPULATION_READ_ROLES,
    apply_household_scope,
    household_visible_to,
    is_national_role,
)

router = APIRouter(prefix="/population", tags=["population"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_population_reader(user: User) -> None:
    if user.role not in POPULATION_READ_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient role permissions")


def _get_household_or_404(db: Session, household_id: int) -> Household:
    household = db.scalar(select(Household).where(Household.id == household_id))
    if household is None:
        raise HTTPException(status_code=404, detail="Household not found")
    return household


def _ensure_visible(user: User, household: Household) -> None:
    if not household_visible_to(user, household):
        # Do not leak existence; mimic 404 for unauthorised access.
        raise HTTPException(status_code=404, detail="Household not found")


def _log_event(
    db: Session,
    *,
    event_type: str,
    actor_user_id: int | None,
    household_id: int | None = None,
    person_id: int | None = None,
    change_request_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    db.add(
        PopulationEventLog(
            event_type=event_type,
            actor_user_id=actor_user_id,
            household_id=household_id,
            person_id=person_id,
            change_request_id=change_request_id,
            payload=payload or {},
            created_at=datetime.now(timezone.utc),
        )
    )


# ---------------------------------------------------------------------------
# Households
# ---------------------------------------------------------------------------


@router.get("/households", response_model=list[HouseholdPublic])
def list_households(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    verification_status: HouseholdVerificationStatus | None = None,
    include_archived: bool = False,
) -> list[Household]:
    _require_population_reader(current_user)
    query = select(Household)
    if not include_archived:
        query = query.where(Household.is_archived.is_(False))
    if verification_status is not None:
        query = query.where(Household.verification_status == verification_status)
    query = apply_household_scope(query, current_user)
    return list(db.scalars(query.order_by(Household.id.desc())))


@router.post("/households", response_model=HouseholdPublic, status_code=201)
def create_household(
    payload: HouseholdCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Household:
    if current_user.role not in DIRECT_REGISTRY_WRITE_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient role permissions")

    # Scope guard: governor / municipality_chief may only create within their scope.
    if current_user.role == UserRole.governor:
        if payload.governorate_id != current_user.governorate_id:
            raise HTTPException(status_code=403, detail="Out of governorate scope")
    if current_user.role == UserRole.municipality_chief:
        if payload.municipality_id != current_user.municipality_id:
            raise HTTPException(status_code=403, detail="Out of municipality scope")

    if db.scalar(select(Household).where(Household.code == payload.code)):
        raise HTTPException(status_code=400, detail="Household code already exists")

    household = Household(
        code=payload.code,
        address_line=payload.address_line,
        governorate_id=payload.governorate_id,
        municipality_id=payload.municipality_id,
        district_id=payload.district_id,
        neighborhood_id=payload.neighborhood_id,
        assigned_mukhtar_user_id=payload.assigned_mukhtar_user_id,
        head_user_id=payload.head_user_id,
        verification_status=HouseholdVerificationStatus.pending,
    )
    db.add(household)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="population.household.create",
        entity_type="household",
        entity_id=str(household.id),
        metadata={"code": household.code},
    )
    _log_event(
        db,
        event_type="household.created",
        actor_user_id=current_user.id,
        household_id=household.id,
        payload={"code": household.code},
    )
    db.commit()
    db.refresh(household)
    return household


@router.get("/households/{household_id}", response_model=HouseholdDetail)
def get_household(
    household_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> HouseholdDetail:
    _require_population_reader(current_user)
    household = _get_household_or_404(db, household_id)
    _ensure_visible(current_user, household)
    members = list(
        db.scalars(
            select(Person)
            .where(Person.household_id == household_id, Person.is_archived.is_(False))
            .order_by(Person.id.asc())
        )
    )
    base = HouseholdPublic.model_validate(household).model_dump()
    return HouseholdDetail(
        **base,
        members=[PersonPublic.model_validate(m) for m in members],
    )


@router.patch("/households/{household_id}", response_model=HouseholdPublic)
def update_household(
    household_id: int,
    payload: HouseholdUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Household:
    if current_user.role not in DIRECT_REGISTRY_WRITE_ROLES and current_user.role != UserRole.mukhtar:
        raise HTTPException(status_code=403, detail="Insufficient role permissions")
    household = _get_household_or_404(db, household_id)
    _ensure_visible(current_user, household)

    # Mukhtars may only update verification_status (verify or reject).
    if current_user.role == UserRole.mukhtar:
        allowed_fields = {"verification_status"}
        provided = {k for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
        if not provided.issubset(allowed_fields):
            raise HTTPException(
                status_code=403,
                detail="Mukhtar may only update verification_status",
            )

    data = payload.model_dump(exclude_unset=True)
    changed: dict[str, Any] = {}
    for field, value in data.items():
        if value is None:
            continue
        if getattr(household, field) != value:
            changed[field] = {"old": getattr(household, field), "new": value}
            setattr(household, field, value)

    if changed:
        write_audit_log(
            db,
            actor_user_id=current_user.id,
            action="population.household.update",
            entity_type="household",
            entity_id=str(household.id),
            metadata={"changes": {k: {"old": str(v["old"]), "new": str(v["new"])} for k, v in changed.items()}},
        )
        _log_event(
            db,
            event_type="household.updated",
            actor_user_id=current_user.id,
            household_id=household.id,
            payload={"fields": list(changed.keys())},
        )
    db.commit()
    db.refresh(household)
    return household


# ---------------------------------------------------------------------------
# Persons
# ---------------------------------------------------------------------------


@router.get("/persons", response_model=list[PersonPublic])
def list_persons(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    household_id: int | None = None,
    include_archived: bool = False,
) -> list[Person]:
    _require_population_reader(current_user)

    # Identify visible household ids first.
    visible_ids_query = apply_household_scope(select(Household.id), current_user)
    if household_id is not None:
        visible_ids_query = visible_ids_query.where(Household.id == household_id)
    visible_ids = list(db.scalars(visible_ids_query))
    if not visible_ids:
        return []

    query = select(Person).where(Person.household_id.in_(visible_ids))
    if not include_archived:
        query = query.where(Person.is_archived.is_(False))
    return list(db.scalars(query.order_by(Person.id.asc())))


@router.post("/persons", response_model=PersonPublic, status_code=201)
def create_person(
    payload: PersonCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Person:
    # Citizens / household_head users may NOT create person records directly.
    if current_user.role not in DIRECT_REGISTRY_WRITE_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Direct creation requires submitting a change request",
        )
    household = _get_household_or_404(db, payload.household_id)
    _ensure_visible(current_user, household)

    person = Person(
        household_id=payload.household_id,
        full_name=payload.full_name,
        birth_date=payload.birth_date,
        gender=payload.gender,
        relation_to_head=payload.relation_to_head,
        national_id=payload.national_id,
        digital_identity_ref=payload.digital_identity_ref,
    )
    db.add(person)
    db.flush()

    # Auto-link a head if the household has none and this person is the self.
    if household.head_person_id is None and payload.relation_to_head == RelationToHead.self:
        household.head_person_id = person.id

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="population.person.create",
        entity_type="person",
        entity_id=str(person.id),
        metadata={"household_id": person.household_id},
    )
    _log_event(
        db,
        event_type="person.created",
        actor_user_id=current_user.id,
        household_id=person.household_id,
        person_id=person.id,
    )
    db.commit()
    db.refresh(person)
    return person


# ---------------------------------------------------------------------------
# Change requests
# ---------------------------------------------------------------------------


def _allowed_submitters() -> set[UserRole]:
    return {
        UserRole.citizen,
        UserRole.household_head,
        UserRole.mukhtar,
        UserRole.municipality_chief,
        UserRole.governor,
        UserRole.admin,
        UserRole.super_admin,
    }


@router.post("/change-requests", response_model=ChangeRequestPublic, status_code=201)
def submit_change_request(
    payload: ChangeRequestCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PopulationChangeRequest:
    if current_user.role not in _allowed_submitters():
        raise HTTPException(status_code=403, detail="Insufficient role permissions")

    household = _get_household_or_404(db, payload.household_id)

    # Citizens & household_head may only submit for households they own.
    if current_user.role in {UserRole.citizen, UserRole.household_head}:
        if household.head_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You may only submit requests for your own household")

    if payload.target_person_id is not None:
        person = db.scalar(select(Person).where(Person.id == payload.target_person_id))
        if person is None or person.household_id != household.id:
            raise HTTPException(status_code=400, detail="Target person does not belong to household")

    cr = PopulationChangeRequest(
        request_type=payload.request_type,
        status=ChangeRequestStatus.mukhtar_review,
        submitted_by_user_id=current_user.id,
        household_id=household.id,
        target_person_id=payload.target_person_id,
        payload=payload.payload,
        reason=payload.reason,
    )
    db.add(cr)
    db.flush()

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="population.change_request.submit",
        entity_type="population_change_request",
        entity_id=str(cr.id),
        metadata={"type": cr.request_type.value, "household_id": household.id},
    )
    _log_event(
        db,
        event_type="change_request.submitted",
        actor_user_id=current_user.id,
        household_id=household.id,
        person_id=payload.target_person_id,
        change_request_id=cr.id,
        payload={"type": cr.request_type.value},
    )

    # Notify the assigned mukhtar (if any).
    if household.assigned_mukhtar_user_id is not None:
        db.add(
            Notification(
                user_id=household.assigned_mukhtar_user_id,
                message=f"طلب تغيير سكاني جديد رقم {cr.id} بانتظار المراجعة",
            )
        )

    db.commit()
    db.refresh(cr)
    return cr


@router.get("/change-requests", response_model=list[ChangeRequestPublic])
def list_change_requests(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status: ChangeRequestStatus | None = Query(default=None),
) -> list[PopulationChangeRequest]:
    if current_user.role not in POPULATION_READ_ROLES and current_user.role != UserRole.citizen:
        raise HTTPException(status_code=403, detail="Insufficient role permissions")

    # Identify visible household ids for this user (citizens see only requests
    # they personally submitted).
    if current_user.role == UserRole.citizen:
        query = select(PopulationChangeRequest).where(
            PopulationChangeRequest.submitted_by_user_id == current_user.id
        )
    else:
        visible_ids = list(db.scalars(apply_household_scope(select(Household.id), current_user)))
        if not visible_ids:
            return []
        query = select(PopulationChangeRequest).where(
            PopulationChangeRequest.household_id.in_(visible_ids)
        )
    if status is not None:
        query = query.where(PopulationChangeRequest.status == status)
    return list(db.scalars(query.order_by(PopulationChangeRequest.id.desc())))


def _apply_change_to_registry(
    db: Session, cr: PopulationChangeRequest, actor_user_id: int
) -> None:
    """Materialise an approved change request onto the registry."""
    household = db.scalar(select(Household).where(Household.id == cr.household_id))
    if household is None:
        return

    rt = cr.request_type
    payload = cr.payload or {}

    if rt == ChangeRequestType.birth or rt == ChangeRequestType.add_member:
        full_name = (payload.get("full_name") or "").strip()
        if not full_name:
            # Reject the change at apply-time rather than silently storing a
            # placeholder. The reviewer should re-submit with a valid payload.
            raise HTTPException(
                status_code=400,
                detail="Change request payload must include a non-empty full_name",
            )
        gender_raw = payload.get("gender", "male")
        try:
            gender = Gender(gender_raw)
        except ValueError:
            gender = Gender.male
        if rt == ChangeRequestType.birth:
            default_relation = "child"
        else:
            default_relation = "other"
        relation_raw = payload.get("relation_to_head", default_relation)
        try:
            relation = RelationToHead(relation_raw)
        except ValueError:
            relation = RelationToHead.other
        birth_str = payload.get("birth_date")
        birth_value: date | None = None
        if birth_str:
            try:
                birth_value = date.fromisoformat(birth_str)
            except ValueError:
                birth_value = None
        person = Person(
            household_id=household.id,
            full_name=full_name,
            birth_date=birth_value,
            gender=gender,
            relation_to_head=relation,
            national_id=payload.get("national_id"),
        )
        db.add(person)
        db.flush()
        cr.target_person_id = person.id
        _log_event(
            db,
            event_type="person.born" if rt == ChangeRequestType.birth else "person.added",
            actor_user_id=actor_user_id,
            household_id=household.id,
            person_id=person.id,
            change_request_id=cr.id,
        )
    elif rt == ChangeRequestType.death:
        if cr.target_person_id is not None:
            person = db.scalar(select(Person).where(Person.id == cr.target_person_id))
            if person is not None:
                person.life_status = LifeStatus.deceased
                death_str = payload.get("death_date")
                if death_str:
                    try:
                        person.death_date = date.fromisoformat(death_str)
                    except ValueError:
                        person.death_date = date.today()
                else:
                    person.death_date = date.today()
                _log_event(
                    db,
                    event_type="person.deceased",
                    actor_user_id=actor_user_id,
                    household_id=household.id,
                    person_id=person.id,
                    change_request_id=cr.id,
                )
    elif rt == ChangeRequestType.remove_member:
        if cr.target_person_id is not None:
            person = db.scalar(select(Person).where(Person.id == cr.target_person_id))
            if person is not None:
                person.is_archived = True
                _log_event(
                    db,
                    event_type="person.removed",
                    actor_user_id=actor_user_id,
                    household_id=household.id,
                    person_id=person.id,
                    change_request_id=cr.id,
                )
    elif rt == ChangeRequestType.address_change:
        new_address = payload.get("address_line")
        if new_address:
            household.address_line = new_address
        for fld in ("governorate_id", "municipality_id", "district_id", "neighborhood_id"):
            if fld in payload and payload[fld] is not None:
                setattr(household, fld, payload[fld])
        _log_event(
            db,
            event_type="household.address_changed",
            actor_user_id=actor_user_id,
            household_id=household.id,
            change_request_id=cr.id,
            payload={"new_address": household.address_line},
        )
    elif rt == ChangeRequestType.correction:
        if cr.target_person_id is not None:
            person = db.scalar(select(Person).where(Person.id == cr.target_person_id))
            if person is not None:
                for fld in ("full_name", "national_id", "digital_identity_ref"):
                    if fld in payload and payload[fld] is not None:
                        setattr(person, fld, payload[fld])
                if "birth_date" in payload and payload["birth_date"]:
                    try:
                        person.birth_date = date.fromisoformat(payload["birth_date"])
                    except ValueError:
                        pass
                _log_event(
                    db,
                    event_type="person.corrected",
                    actor_user_id=actor_user_id,
                    household_id=household.id,
                    person_id=person.id,
                    change_request_id=cr.id,
                )


@router.post("/change-requests/{request_id}/mukhtar-decision", response_model=ChangeRequestPublic)
def mukhtar_decision(
    request_id: int,
    payload: ChangeRequestDecision,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.mukhtar))],
) -> PopulationChangeRequest:
    cr = db.scalar(select(PopulationChangeRequest).where(PopulationChangeRequest.id == request_id))
    if cr is None:
        raise HTTPException(status_code=404, detail="Change request not found")
    household = _get_household_or_404(db, cr.household_id)
    _ensure_visible(current_user, household)
    if cr.status != ChangeRequestStatus.mukhtar_review:
        raise HTTPException(status_code=400, detail="Request is not awaiting mukhtar review")

    cr.mukhtar_user_id = current_user.id
    cr.mukhtar_decision_at = datetime.now(timezone.utc)
    cr.mukhtar_comment = payload.comment

    if not payload.approve:
        cr.status = ChangeRequestStatus.rejected
        action = "population.change_request.mukhtar_reject"
    elif cr.request_type.value in HIGH_RISK_CHANGE_TYPES:
        cr.status = ChangeRequestStatus.municipality_review
        action = "population.change_request.mukhtar_forward"
    else:
        cr.status = ChangeRequestStatus.approved
        action = "population.change_request.mukhtar_approve"
        _apply_change_to_registry(db, cr, current_user.id)

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action=action,
        entity_type="population_change_request",
        entity_id=str(cr.id),
        metadata={"approve": payload.approve, "type": cr.request_type.value},
    )
    db.add(
        Notification(
            user_id=cr.submitted_by_user_id,
            message=f"تم تحديث حالة طلب التغيير رقم {cr.id} إلى {cr.status.value}",
        )
    )
    db.commit()
    db.refresh(cr)
    return cr


@router.post("/change-requests/{request_id}/municipality-decision", response_model=ChangeRequestPublic)
def municipality_decision(
    request_id: int,
    payload: ChangeRequestDecision,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.municipality_chief, UserRole.governor, UserRole.super_admin, UserRole.admin)),
    ],
) -> PopulationChangeRequest:
    cr = db.scalar(select(PopulationChangeRequest).where(PopulationChangeRequest.id == request_id))
    if cr is None:
        raise HTTPException(status_code=404, detail="Change request not found")
    household = _get_household_or_404(db, cr.household_id)
    _ensure_visible(current_user, household)
    if cr.status != ChangeRequestStatus.municipality_review:
        raise HTTPException(status_code=400, detail="Request is not awaiting municipality review")

    cr.municipality_user_id = current_user.id
    cr.municipality_decision_at = datetime.now(timezone.utc)
    cr.municipality_comment = payload.comment

    if payload.approve:
        cr.status = ChangeRequestStatus.approved
        _apply_change_to_registry(db, cr, current_user.id)
        action = "population.change_request.municipality_approve"
    else:
        cr.status = ChangeRequestStatus.rejected
        action = "population.change_request.municipality_reject"

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action=action,
        entity_type="population_change_request",
        entity_id=str(cr.id),
        metadata={"approve": payload.approve, "type": cr.request_type.value},
    )
    db.add(
        Notification(
            user_id=cr.submitted_by_user_id,
            message=f"تم تحديث حالة طلب التغيير رقم {cr.id} إلى {cr.status.value}",
        )
    )
    db.commit()
    db.refresh(cr)
    return cr


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def _age_from_birth(birth: date | None, today: date) -> int | None:
    if birth is None:
        return None
    years = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    return max(years, 0)


@router.get("/statistics", response_model=PopulationStatistics)
def population_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PopulationStatistics:
    _require_population_reader(current_user)

    visible_household_ids = list(db.scalars(apply_household_scope(select(Household.id), current_user)))

    if not visible_household_ids:
        return PopulationStatistics(
            scope_label=_scope_label(current_user, db),
            total_population=0,
            total_households=0,
            verified_households=0,
            pending_households=0,
            births_last_year=0,
            deaths_last_year=0,
            age_groups=[],
            gender=GenderBreakdown(),
            requests_by_status=[],
            administrative_breakdown=[],
        )

    households = list(
        db.scalars(select(Household).where(Household.id.in_(visible_household_ids)))
    )
    persons = list(
        db.scalars(
            select(Person).where(
                Person.household_id.in_(visible_household_ids),
                Person.is_archived.is_(False),
            )
        )
    )

    today = date.today()
    one_year_ago = today - timedelta(days=365)

    total_population = sum(1 for p in persons if p.life_status == LifeStatus.alive)
    verified = sum(1 for h in households if h.verification_status == HouseholdVerificationStatus.verified)
    pending = sum(1 for h in households if h.verification_status == HouseholdVerificationStatus.pending)

    births_last_year = sum(1 for p in persons if p.birth_date and p.birth_date >= one_year_ago)
    deaths_last_year = sum(
        1
        for p in persons
        if p.life_status == LifeStatus.deceased and p.death_date and p.death_date >= one_year_ago
    )

    bands = [(0, 4, "0-4"), (5, 14, "5-14"), (15, 24, "15-24"), (25, 44, "25-44"), (45, 64, "45-64"), (65, 200, "65+")]
    counts = {label: 0 for _, _, label in bands}
    unknown = 0
    male = 0
    female = 0
    for p in persons:
        if p.life_status != LifeStatus.alive:
            continue
        if p.gender == Gender.male:
            male += 1
        elif p.gender == Gender.female:
            female += 1
        age = _age_from_birth(p.birth_date, today)
        if age is None:
            unknown += 1
            continue
        for low, high, label in bands:
            if low <= age <= high:
                counts[label] += 1
                break
    age_groups = [AgeGroupBreakdown(label=lbl, count=counts[lbl]) for _, _, lbl in bands]
    if unknown:
        age_groups.append(AgeGroupBreakdown(label="غير معروف", count=unknown))

    # Requests by status (scoped to visible households).
    cr_rows = list(
        db.scalars(
            select(PopulationChangeRequest).where(
                PopulationChangeRequest.household_id.in_(visible_household_ids)
            )
        )
    )
    cr_counts: dict[str, int] = {}
    for cr in cr_rows:
        cr_counts[cr.status.value] = cr_counts.get(cr.status.value, 0) + 1
    requests_by_status = [StatusBreakdown(label=k, count=v) for k, v in sorted(cr_counts.items())]

    # Administrative breakdown depends on the role:
    #   - super_admin / admin: per-governorate
    #   - governor: per-municipality within their governorate
    #   - municipality_chief: per-district within their municipality
    #   - others: empty list
    admin_breakdown: list[AdministrativeBreakdownItem] = []
    if is_national_role(current_user.role):
        rows = db.execute(
            select(
                Governorate.id,
                Governorate.name_ar,
                func.count(func.distinct(Household.id)),
                func.count(Person.id),
            )
            .join(Household, Household.governorate_id == Governorate.id, isouter=True)
            .join(
                Person,
                (Person.household_id == Household.id) & (Person.is_archived.is_(False)),
                isouter=True,
            )
            .group_by(Governorate.id, Governorate.name_ar)
            .order_by(Governorate.id)
        ).all()
        admin_breakdown = [
            AdministrativeBreakdownItem(id=r[0], name_ar=r[1], households=int(r[2] or 0), population=int(r[3] or 0))
            for r in rows
        ]
    elif current_user.role == UserRole.governor and current_user.governorate_id:
        rows = db.execute(
            select(
                Municipality.id,
                Municipality.name_ar,
                func.count(func.distinct(Household.id)),
                func.count(Person.id),
            )
            .join(Household, Household.municipality_id == Municipality.id, isouter=True)
            .join(
                Person,
                (Person.household_id == Household.id) & (Person.is_archived.is_(False)),
                isouter=True,
            )
            .where(Municipality.governorate_id == current_user.governorate_id)
            .group_by(Municipality.id, Municipality.name_ar)
            .order_by(Municipality.id)
        ).all()
        admin_breakdown = [
            AdministrativeBreakdownItem(id=r[0], name_ar=r[1], households=int(r[2] or 0), population=int(r[3] or 0))
            for r in rows
        ]

    return PopulationStatistics(
        scope_label=_scope_label(current_user, db),
        total_population=total_population,
        total_households=len(households),
        verified_households=verified,
        pending_households=pending,
        births_last_year=births_last_year,
        deaths_last_year=deaths_last_year,
        age_groups=age_groups,
        gender=GenderBreakdown(male=male, female=female),
        requests_by_status=requests_by_status,
        administrative_breakdown=admin_breakdown,
    )


def _scope_label(user: User, db: Session) -> str:
    if is_national_role(user.role):
        return "كامل الجمهورية العربية السورية"
    if user.role == UserRole.governor and user.governorate_id:
        gov = db.scalar(select(Governorate).where(Governorate.id == user.governorate_id))
        return f"محافظة {gov.name_ar}" if gov else "نطاق المحافظة"
    if user.role == UserRole.municipality_chief and user.municipality_id:
        mun = db.scalar(select(Municipality).where(Municipality.id == user.municipality_id))
        return f"بلدية {mun.name_ar}" if mun else "نطاق البلدية"
    if user.role == UserRole.mukhtar:
        return "نطاق المختار"
    if user.role == UserRole.household_head:
        return "الأسرة"
    return "نطاق محدود"
