"""Service layer for the Phase-2 population change-request workflow.

Centralises all business logic for the request life-cycle:

    create_change_request → submitted
    review_change_request → under_review | rejected | approved
    approve_change_request → approved (and applies the change)
    cancel_change_request  → cancelled
    apply_change_request   → materialises an approved request onto the registry

Routes should remain thin and delegate to these functions.

Notes:
* The legacy Phase-1 statuses `mukhtar_review` and `municipality_review` are
  treated as sub-states of `under_review` so the new service can operate
  uniformly on both old and new requests.
* All mutating operations write a row in `audit_logs` (generic) and in
  `population_event_logs` (population-specific). They do NOT call
  `db.commit()` themselves — the caller controls the transaction boundary.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.population import (
    ChangeRequestStatus,
    ChangeRequestType,
    Gender,
    Household,
    LifeStatus,
    Person,
    PopulationChangeRequest,
    PopulationEventLog,
    RelationToHead,
)
from app.models.user import User, UserRole
from app.services.audit import write_audit_log
from app.services.population_rbac import (
    HIGH_RISK_CHANGE_TYPES,
    household_visible_to,
    is_national_role,
)


# ---------------------------------------------------------------------------
# Role groupings
# ---------------------------------------------------------------------------

# Roles allowed to submit a change request via POST /change-requests.
SUBMITTER_ROLES = {
    UserRole.household_head,
    UserRole.mukhtar,
    UserRole.admin,
    UserRole.super_admin,
}

# Roles allowed to perform the review step (start/reject and — for low-risk
# requests — approve as well via /review). municipality_chief, admin and
# super_admin can additionally approve via /approve.
REVIEW_ROLES = {
    UserRole.mukhtar,
    UserRole.municipality_chief,
    UserRole.admin,
    UserRole.super_admin,
}

# Roles allowed to perform the final approval step.
APPROVE_ROLES = {
    UserRole.municipality_chief,
    UserRole.admin,
    UserRole.super_admin,
}

# Statuses that mean "already finalised" — no further state transitions
# allowed except possibly an admin re-open (out of scope for Phase 2).
TERMINAL_STATUSES = {
    ChangeRequestStatus.approved,
    ChangeRequestStatus.rejected,
    ChangeRequestStatus.cancelled,
}

# Statuses that count as "under review" for transition purposes — the
# Phase-1 mukhtar_review / municipality_review are folded in here so that
# legacy requests continue to flow through the unified review/approve
# endpoints.
REVIEWING_STATUSES = {
    ChangeRequestStatus.under_review,
    ChangeRequestStatus.mukhtar_review,
    ChangeRequestStatus.municipality_review,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


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
            created_at=_now(),
        )
    )


def generate_request_number(db: Session) -> str:
    """Return a unique human-friendly request number `CR-YYYY-NNNNNN`.

    Uses the current count of requests + 1 for the sequential portion.
    Collisions are extremely unlikely given the year prefix; if one occurs
    the caller may simply retry.
    """
    year = _now().year
    seq = (db.scalar(select(func.count()).select_from(PopulationChangeRequest)) or 0) + 1
    return f"CR-{year}-{seq:06d}"


def _ensure_household_visible(user: User, household: Household) -> None:
    if not household_visible_to(user, household):
        # Mask as 404 to avoid leaking existence.
        raise HTTPException(status_code=404, detail="Household not found")


def _get_request_or_404(db: Session, request_id: int) -> PopulationChangeRequest:
    cr = db.scalar(
        select(PopulationChangeRequest).where(PopulationChangeRequest.id == request_id)
    )
    if cr is None:
        raise HTTPException(status_code=404, detail="Change request not found")
    return cr


def request_visible_to(db: Session, user: User, cr: PopulationChangeRequest) -> bool:
    """Return True when `user` is allowed to read this change request."""
    if user.role in {UserRole.super_admin, UserRole.admin}:
        return True
    household = db.scalar(select(Household).where(Household.id == cr.household_id))
    if household is None:
        return False
    if user.role == UserRole.household_head:
        return household.head_user_id == user.id
    return household_visible_to(user, household)


# ---------------------------------------------------------------------------
# create_change_request
# ---------------------------------------------------------------------------


def create_change_request(
    db: Session,
    *,
    current_user: User,
    request_type: ChangeRequestType,
    household_id: int,
    person_id: int | None = None,
    payload: dict[str, Any] | None = None,
    reason: str | None = None,
    initial_status: ChangeRequestStatus = ChangeRequestStatus.submitted,
) -> PopulationChangeRequest:
    """Create a new change request after validating role + scope + duplicates.

    `initial_status` may be overridden by callers preserving Phase-1 wire
    behaviour (which sets `mukhtar_review`).
    """
    if current_user.role not in SUBMITTER_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient role permissions")

    household = db.scalar(select(Household).where(Household.id == household_id))
    if household is None:
        raise HTTPException(status_code=404, detail="Household not found")

    # household_head may only create requests for their own household.
    if current_user.role == UserRole.household_head:
        if household.head_user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You may only submit requests for your own household",
            )

    # mukhtar may only create requests for households visible in their scope.
    if current_user.role == UserRole.mukhtar:
        if not household_visible_to(current_user, household):
            raise HTTPException(status_code=404, detail="Household not found")

    if person_id is not None:
        person = db.scalar(select(Person).where(Person.id == person_id))
        if person is None or person.household_id != household.id:
            raise HTTPException(
                status_code=400, detail="Target person does not belong to household"
            )

    # Prevent duplicate pending birth/death requests for the same target.
    if request_type in {ChangeRequestType.birth, ChangeRequestType.death}:
        dup_query = select(PopulationChangeRequest).where(
            PopulationChangeRequest.household_id == household.id,
            PopulationChangeRequest.request_type == request_type,
            PopulationChangeRequest.status.in_(
                [
                    ChangeRequestStatus.draft,
                    ChangeRequestStatus.submitted,
                    ChangeRequestStatus.under_review,
                    ChangeRequestStatus.mukhtar_review,
                    ChangeRequestStatus.municipality_review,
                ]
            ),
        )
        if request_type == ChangeRequestType.death and person_id is not None:
            dup_query = dup_query.where(
                PopulationChangeRequest.target_person_id == person_id
            )
        if db.scalar(dup_query) is not None:
            raise HTTPException(
                status_code=409,
                detail="A pending request of this type already exists",
            )

    cr = PopulationChangeRequest(
        request_number=generate_request_number(db),
        request_type=request_type,
        status=initial_status,
        submitted_by_user_id=current_user.id,
        household_id=household.id,
        target_person_id=person_id,
        payload=payload or {},
        reason=reason,
    )
    db.add(cr)
    db.flush()

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="population.change_request.submit",
        entity_type="population_change_request",
        entity_id=str(cr.id),
        metadata={
            "type": cr.request_type.value,
            "household_id": household.id,
            "request_number": cr.request_number,
        },
    )
    _log_event(
        db,
        event_type="change_request.submitted",
        actor_user_id=current_user.id,
        household_id=household.id,
        person_id=person_id,
        change_request_id=cr.id,
        payload={"type": cr.request_type.value},
    )

    if household.assigned_mukhtar_user_id is not None:
        db.add(
            Notification(
                user_id=household.assigned_mukhtar_user_id,
                message=f"طلب تغيير سكاني جديد رقم {cr.request_number or cr.id} بانتظار المراجعة",
            )
        )

    return cr


# ---------------------------------------------------------------------------
# review_change_request
# ---------------------------------------------------------------------------


def _ensure_can_review(user: User, cr: PopulationChangeRequest, household: Household) -> None:
    if user.role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient role permissions")
    if not household_visible_to(user, household):
        raise HTTPException(
            status_code=403, detail="Cannot review requests outside your scope"
        )


def review_change_request(
    db: Session,
    *,
    request_id: int,
    current_user: User,
    action: str,
    review_notes: str | None = None,
    rejection_reason: str | None = None,
) -> PopulationChangeRequest:
    """Apply a reviewer action: `start`, `approve`, or `reject`."""
    cr = _get_request_or_404(db, request_id)
    household = db.scalar(select(Household).where(Household.id == cr.household_id))
    if household is None:
        raise HTTPException(status_code=404, detail="Household not found")
    _ensure_can_review(current_user, cr, household)

    if cr.status in TERMINAL_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Request is already finalised and cannot be reviewed",
        )

    cr.reviewed_by_user_id = current_user.id
    cr.reviewed_at = _now()
    if review_notes is not None:
        cr.review_notes = review_notes

    if action == "start":
        cr.status = ChangeRequestStatus.under_review
        audit_action = "population.change_request.review_start"
    elif action == "reject":
        if not rejection_reason or not rejection_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection requires a non-empty rejection_reason",
            )
        cr.status = ChangeRequestStatus.rejected
        cr.rejection_reason = rejection_reason.strip()
        audit_action = "population.change_request.reject"
    elif action == "approve":
        # The /review endpoint may finalise low-risk requests directly when
        # the actor is mukhtar/admin/super_admin. Higher-risk changes must
        # go through /approve so a municipality_chief (or higher) is on
        # record as the approver.
        if current_user.role == UserRole.mukhtar and cr.request_type.value in HIGH_RISK_CHANGE_TYPES:
            raise HTTPException(
                status_code=403,
                detail="High-risk requests must be approved by a municipality chief",
            )
        cr.approved_by_user_id = current_user.id
        cr.approved_at = _now()
        cr.status = ChangeRequestStatus.approved
        apply_change_request(db, cr, actor_user_id=current_user.id)
        audit_action = "population.change_request.approve"
    else:
        raise HTTPException(status_code=400, detail="Unknown review action")

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action=audit_action,
        entity_type="population_change_request",
        entity_id=str(cr.id),
        metadata={
            "action": action,
            "type": cr.request_type.value,
            "status": cr.status.value,
        },
    )
    _log_event(
        db,
        event_type=f"change_request.{action}",
        actor_user_id=current_user.id,
        household_id=cr.household_id,
        person_id=cr.target_person_id,
        change_request_id=cr.id,
        payload={"status": cr.status.value},
    )
    db.add(
        Notification(
            user_id=cr.submitted_by_user_id,
            message=f"تم تحديث حالة طلب التغيير رقم {cr.request_number or cr.id} إلى {cr.status.value}",
        )
    )
    return cr


# ---------------------------------------------------------------------------
# approve_change_request
# ---------------------------------------------------------------------------


def approve_change_request(
    db: Session,
    *,
    request_id: int,
    current_user: User,
    review_notes: str | None = None,
) -> PopulationChangeRequest:
    """Final approval — only municipality_chief / admin / super_admin.

    The actor must have access to the household. For mukhtar approval of
    low-risk requests use /review with action=approve instead.
    """
    cr = _get_request_or_404(db, request_id)

    if current_user.role not in APPROVE_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient role permissions")

    household = db.scalar(select(Household).where(Household.id == cr.household_id))
    if household is None:
        raise HTTPException(status_code=404, detail="Household not found")
    if not household_visible_to(current_user, household):
        raise HTTPException(
            status_code=403, detail="Cannot approve requests outside your scope"
        )

    if cr.status == ChangeRequestStatus.approved:
        raise HTTPException(status_code=400, detail="Request is already approved")
    if cr.status == ChangeRequestStatus.rejected:
        # A rejected request can only be re-opened by admin / super_admin —
        # not handled by /approve for now.
        raise HTTPException(
            status_code=400,
            detail="Rejected requests cannot be approved without being reopened",
        )
    if cr.status == ChangeRequestStatus.cancelled:
        raise HTTPException(status_code=400, detail="Cancelled requests cannot be approved")

    cr.approved_by_user_id = current_user.id
    cr.approved_at = _now()
    if review_notes is not None:
        cr.review_notes = review_notes
    cr.status = ChangeRequestStatus.approved

    apply_change_request(db, cr, actor_user_id=current_user.id)

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="population.change_request.approve",
        entity_type="population_change_request",
        entity_id=str(cr.id),
        metadata={"type": cr.request_type.value, "status": cr.status.value},
    )
    _log_event(
        db,
        event_type="change_request.approved",
        actor_user_id=current_user.id,
        household_id=cr.household_id,
        person_id=cr.target_person_id,
        change_request_id=cr.id,
        payload={"type": cr.request_type.value},
    )
    db.add(
        Notification(
            user_id=cr.submitted_by_user_id,
            message=f"تمت الموافقة على طلب التغيير رقم {cr.request_number or cr.id}",
        )
    )
    return cr


# ---------------------------------------------------------------------------
# cancel_change_request
# ---------------------------------------------------------------------------


def cancel_change_request(
    db: Session,
    *,
    request_id: int,
    current_user: User,
) -> PopulationChangeRequest:
    """Cancel a non-finalised request.

    Allowed actors:
        * the original submitter (before the request is approved/rejected)
        * admin / super_admin (always, while not yet finalised)
    """
    cr = _get_request_or_404(db, request_id)

    if cr.status in TERMINAL_STATUSES:
        raise HTTPException(status_code=400, detail="Request is already finalised")

    is_owner = cr.submitted_by_user_id == current_user.id
    is_admin = current_user.role in {UserRole.admin, UserRole.super_admin}
    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Only the owner or an admin may cancel")

    cr.status = ChangeRequestStatus.cancelled

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="population.change_request.cancel",
        entity_type="population_change_request",
        entity_id=str(cr.id),
        metadata={"type": cr.request_type.value},
    )
    _log_event(
        db,
        event_type="change_request.cancelled",
        actor_user_id=current_user.id,
        household_id=cr.household_id,
        person_id=cr.target_person_id,
        change_request_id=cr.id,
    )
    return cr


# ---------------------------------------------------------------------------
# apply_change_request — materialise an approved request onto the registry
# ---------------------------------------------------------------------------


# Correction fields a non-admin reviewer may modify.
_PUBLIC_CORRECTION_FIELDS = {"full_name", "birth_date", "digital_identity_ref"}
# Additional fields only admin / super_admin may modify via correction.
_PROTECTED_CORRECTION_FIELDS = {"national_id", "gender"}


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def apply_change_request(
    db: Session, cr: PopulationChangeRequest, *, actor_user_id: int
) -> None:
    """Materialise an approved change request onto the live registry.

    The function assumes the caller has already authorised the actor and
    set `cr.status = approved`. It is safe to call exactly once per
    approval transition.
    """
    household = db.scalar(select(Household).where(Household.id == cr.household_id))
    if household is None:
        return

    rt = cr.request_type
    payload = cr.payload or {}
    actor = db.scalar(select(User).where(User.id == actor_user_id))

    if rt in (ChangeRequestType.birth, ChangeRequestType.add_member):
        full_name = (payload.get("full_name") or "").strip()
        if not full_name:
            raise HTTPException(
                status_code=400,
                detail="Change request payload must include a non-empty full_name",
            )
        try:
            gender = Gender(payload.get("gender", "male"))
        except ValueError:
            gender = Gender.male
        default_relation = "child" if rt == ChangeRequestType.birth else "other"
        try:
            relation = RelationToHead(payload.get("relation_to_head", default_relation))
        except ValueError:
            relation = RelationToHead.other
        person = Person(
            household_id=household.id,
            full_name=full_name,
            birth_date=_parse_date(payload.get("birth_date")),
            gender=gender,
            relation_to_head=relation,
            national_id=payload.get("national_id"),
            life_status=LifeStatus.alive,
        )
        db.add(person)
        db.flush()
        cr.target_person_id = person.id
        _log_event(
            db,
            event_type="person.added",
            actor_user_id=actor_user_id,
            household_id=household.id,
            person_id=person.id,
            change_request_id=cr.id,
            payload={"birth": rt == ChangeRequestType.birth},
        )

    elif rt == ChangeRequestType.death:
        if cr.target_person_id is None:
            raise HTTPException(
                status_code=400,
                detail="Death requests require a target person",
            )
        person = db.scalar(select(Person).where(Person.id == cr.target_person_id))
        if person is None:
            raise HTTPException(status_code=404, detail="Target person not found")
        person.life_status = LifeStatus.deceased
        person.death_date = _parse_date(payload.get("death_date")) or date.today()
        _log_event(
            db,
            event_type="person.deceased",
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
            event_type="address_changed",
            actor_user_id=actor_user_id,
            household_id=household.id,
            change_request_id=cr.id,
            payload={"new_address": household.address_line},
        )

    elif rt == ChangeRequestType.correction:
        if cr.target_person_id is None:
            raise HTTPException(
                status_code=400,
                detail="Correction requests require a target person",
            )
        person = db.scalar(select(Person).where(Person.id == cr.target_person_id))
        if person is None:
            raise HTTPException(status_code=404, detail="Target person not found")
        actor_role = actor.role if actor is not None else None
        is_priv = actor_role in {UserRole.admin, UserRole.super_admin}
        for fld, value in payload.items():
            if value is None:
                continue
            if fld in _PUBLIC_CORRECTION_FIELDS:
                if fld == "birth_date":
                    parsed = _parse_date(value)
                    if parsed is not None:
                        person.birth_date = parsed
                else:
                    setattr(person, fld, value)
            elif fld in _PROTECTED_CORRECTION_FIELDS:
                if not is_priv:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Field '{fld}' may only be corrected by an administrator",
                    )
                if fld == "gender":
                    try:
                        person.gender = Gender(value)
                    except ValueError:
                        pass
                else:
                    setattr(person, fld, value)
            # Silently ignore unknown fields — they were never persisted.
        _log_event(
            db,
            event_type="person.updated",
            actor_user_id=actor_user_id,
            household_id=household.id,
            person_id=person.id,
            change_request_id=cr.id,
        )

    elif rt == ChangeRequestType.remove_member:
        if cr.target_person_id is None:
            raise HTTPException(
                status_code=400,
                detail="remove_member requests require a target person",
            )
        person = db.scalar(select(Person).where(Person.id == cr.target_person_id))
        if person is None:
            raise HTTPException(status_code=404, detail="Target person not found")
        person.is_archived = True
        _log_event(
            db,
            event_type="person.updated",
            actor_user_id=actor_user_id,
            household_id=household.id,
            person_id=person.id,
            change_request_id=cr.id,
            payload={"removed": True},
        )

    elif rt == ChangeRequestType.move_member:
        if cr.target_person_id is None:
            raise HTTPException(
                status_code=400,
                detail="move_member requests require a target person",
            )
        target_household_id = payload.get("target_household_id")
        if not target_household_id:
            raise HTTPException(
                status_code=400,
                detail="move_member payload must include target_household_id",
            )
        target_household = db.scalar(
            select(Household).where(Household.id == target_household_id)
        )
        if target_household is None:
            raise HTTPException(status_code=404, detail="Target household not found")
        person = db.scalar(select(Person).where(Person.id == cr.target_person_id))
        if person is None:
            raise HTTPException(status_code=404, detail="Target person not found")
        # Verify the approving role has access to BOTH households (admins
        # always do).
        if actor is not None and not is_national_role(actor.role):
            if not (
                household_visible_to(actor, household)
                and household_visible_to(actor, target_household)
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Approver must have access to both source and target households",
                )
        source_id = person.household_id
        person.household_id = target_household.id
        _log_event(
            db,
            event_type="person.moved",
            actor_user_id=actor_user_id,
            household_id=source_id,
            person_id=person.id,
            change_request_id=cr.id,
            payload={"to_household_id": target_household.id},
        )
        _log_event(
            db,
            event_type="person.moved",
            actor_user_id=actor_user_id,
            household_id=target_household.id,
            person_id=person.id,
            change_request_id=cr.id,
            payload={"from_household_id": source_id},
        )
