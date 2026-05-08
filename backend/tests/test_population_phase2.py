"""Phase-2 Population Change Requests Workflow tests.

Covers the unified review/approve/cancel workflow on top of Phase-1
RBAC scoping, including audit and event-log assertions.
"""

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.admin_scope import District, Governorate, Municipality, Neighborhood
from app.models.audit import AuditLog
from app.models.population import (
    ChangeRequestStatus,
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


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client, email: str, password: str = "Passw0rd!") -> str:
    resp = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _seed_world():
    """Two-governorate world with all relevant role users."""
    with SessionLocal() as db:
        gov1 = Governorate(code="P2G1", name_ar="غ1")
        gov2 = Governorate(code="P2G2", name_ar="غ2")
        db.add_all([gov1, gov2])
        db.flush()

        mun1 = Municipality(governorate_id=gov1.id, code="P2M1", name_ar="بلدية1")
        mun2 = Municipality(governorate_id=gov2.id, code="P2M2", name_ar="بلدية2")
        db.add_all([mun1, mun2])
        db.flush()

        dist1 = District(municipality_id=mun1.id, code="P2D1", name_ar="منطقة1")
        dist2 = District(municipality_id=mun2.id, code="P2D2", name_ar="منطقة2")
        db.add_all([dist1, dist2])
        db.flush()

        nb1 = Neighborhood(district_id=dist1.id, code="P2N1", name_ar="حي1")
        db.add(nb1)
        db.flush()

        sa = User(
            full_name="SA", email="p2_sa@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.super_admin,
        )
        chief1 = User(
            full_name="Chief1", email="p2_chief1@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.municipality_chief,
            governorate_id=gov1.id, municipality_id=mun1.id,
        )
        chief2 = User(
            full_name="Chief2", email="p2_chief2@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.municipality_chief,
            governorate_id=gov2.id, municipality_id=mun2.id,
        )
        mukhtar1 = User(
            full_name="Mukhtar1", email="p2_mukhtar1@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.mukhtar,
            governorate_id=gov1.id, municipality_id=mun1.id,
            district_id=dist1.id, neighborhood_id=nb1.id,
        )
        mukhtar2 = User(
            full_name="Mukhtar2", email="p2_mukhtar2@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.mukhtar,
            governorate_id=gov2.id, municipality_id=mun2.id,
            district_id=dist2.id,
        )
        head1 = User(
            full_name="Head1", email="p2_head1@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.household_head,
        )
        head2 = User(
            full_name="Head2", email="p2_head2@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.household_head,
        )
        db.add_all([sa, chief1, chief2, mukhtar1, mukhtar2, head1, head2])
        db.flush()

        h1 = Household(
            code="P2H1", address_line="addr1",
            governorate_id=gov1.id, municipality_id=mun1.id,
            district_id=dist1.id, neighborhood_id=nb1.id,
            assigned_mukhtar_user_id=mukhtar1.id,
            head_user_id=head1.id,
            verification_status=HouseholdVerificationStatus.verified,
        )
        h2 = Household(
            code="P2H2", address_line="addr2",
            governorate_id=gov2.id, municipality_id=mun2.id,
            district_id=dist2.id,
            assigned_mukhtar_user_id=mukhtar2.id,
            head_user_id=head2.id,
            verification_status=HouseholdVerificationStatus.verified,
        )
        db.add_all([h1, h2])
        db.flush()

        p1 = Person(
            household_id=h1.id, full_name="Head1 self",
            gender=Gender.male, relation_to_head=RelationToHead.self,
        )
        p2 = Person(
            household_id=h2.id, full_name="Head2 self",
            gender=Gender.female, relation_to_head=RelationToHead.self,
        )
        db.add_all([p1, p2])
        db.commit()
        return {
            "h1_id": h1.id, "h2_id": h2.id,
            "p1_id": p1.id, "p2_id": p2.id,
            "sa_email": sa.email,
            "chief1_email": chief1.email,
            "chief2_email": chief2.email,
            "mukhtar1_email": mukhtar1.email,
            "mukhtar2_email": mukhtar2.email,
            "head1_email": head1.email,
            "head2_email": head2.email,
        }


def _submit_birth(client, head_token: str, household_id: int, name: str = "Newborn") -> int:
    resp = client.post(
        "/api/v1/population/change-requests",
        json={
            "request_type": "birth",
            "household_id": household_id,
            "payload": {
                "full_name": name,
                "gender": "female",
                "relation_to_head": "child",
                "birth_date": "2026-01-01",
            },
        },
        headers=_auth_header(head_token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # New field must be present.
    assert body["request_number"], "request_number must be auto-generated"
    return body["id"]


# ---------------------------------------------------------------------------
# Submission RBAC
# ---------------------------------------------------------------------------


def test_household_head_can_submit_for_own_household(client):
    ids = _seed_world()
    token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, token, ids["h1_id"])

    # Owner can read it back via GET /change-requests/{id}.
    resp = client.get(
        f"/api/v1/population/change-requests/{cr_id}", headers=_auth_header(token)
    )
    assert resp.status_code == 200
    assert resp.json()["household_id"] == ids["h1_id"]


def test_household_head_cannot_submit_for_other_household(client):
    ids = _seed_world()
    token = _login(client, ids["head1_email"])
    resp = client.post(
        "/api/v1/population/change-requests",
        json={
            "request_type": "birth",
            "household_id": ids["h2_id"],
            "payload": {"full_name": "X", "gender": "male"},
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Review RBAC
# ---------------------------------------------------------------------------


def test_mukhtar_can_review_request_in_scope(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, head_token, ids["h1_id"])

    mukhtar_token = _login(client, ids["mukhtar1_email"])
    resp = client.patch(
        f"/api/v1/population/change-requests/{cr_id}/review",
        json={"action": "start", "review_notes": "بدء المراجعة"},
        headers=_auth_header(mukhtar_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == ChangeRequestStatus.under_review.value
    assert body["reviewed_by_user_id"] is not None


def test_mukhtar_cannot_review_outside_scope(client):
    ids = _seed_world()
    head_token = _login(client, ids["head2_email"])
    cr_id = _submit_birth(client, head_token, ids["h2_id"])

    # mukhtar1 belongs to gov1/mun1 — cannot touch H2.
    other_mukhtar_token = _login(client, ids["mukhtar1_email"])
    resp = client.patch(
        f"/api/v1/population/change-requests/{cr_id}/review",
        json={"action": "start"},
        headers=_auth_header(other_mukhtar_token),
    )
    assert resp.status_code == 403


def test_municipality_chief_can_approve_in_municipality(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, head_token, ids["h1_id"], name="ApprovedBaby")

    chief_token = _login(client, ids["chief1_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/approve",
        json={"review_notes": "موافق"},
        headers=_auth_header(chief_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == ChangeRequestStatus.approved.value
    assert body["approved_by_user_id"] is not None
    assert body["approved_at"] is not None


# ---------------------------------------------------------------------------
# Approval application
# ---------------------------------------------------------------------------


def test_approval_of_birth_creates_person(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, head_token, ids["h1_id"], name="BornBaby")

    chief_token = _login(client, ids["chief1_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/approve",
        json={},
        headers=_auth_header(chief_token),
    )
    assert resp.status_code == 200

    # Person row was created in H1.
    with SessionLocal() as db:
        people = (
            db.query(Person)
            .filter(Person.household_id == ids["h1_id"], Person.full_name == "BornBaby")
            .all()
        )
        assert len(people) == 1
        assert people[0].life_status == LifeStatus.alive


def test_approval_of_death_updates_life_status(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    resp = client.post(
        "/api/v1/population/change-requests",
        json={
            "request_type": "death",
            "household_id": ids["h1_id"],
            "person_id": ids["p1_id"],
            "payload": {"death_date": "2026-04-01"},
        },
        headers=_auth_header(head_token),
    )
    assert resp.status_code == 201, resp.text
    cr_id = resp.json()["id"]

    chief_token = _login(client, ids["chief1_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/approve",
        json={},
        headers=_auth_header(chief_token),
    )
    assert resp.status_code == 200

    with SessionLocal() as db:
        person = db.get(Person, ids["p1_id"])
        assert person.life_status == LifeStatus.deceased
        assert person.death_date is not None


def test_approval_of_address_change_updates_household(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    resp = client.post(
        "/api/v1/population/change-requests",
        json={
            "request_type": "address_change",
            "household_id": ids["h1_id"],
            "payload": {"address_line": "عنوان جديد"},
        },
        headers=_auth_header(head_token),
    )
    assert resp.status_code == 201
    cr_id = resp.json()["id"]

    chief_token = _login(client, ids["chief1_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/approve",
        json={},
        headers=_auth_header(chief_token),
    )
    assert resp.status_code == 200

    with SessionLocal() as db:
        household = db.get(Household, ids["h1_id"])
        assert household.address_line == "عنوان جديد"


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------


def test_rejected_request_requires_reason(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, head_token, ids["h1_id"])

    mukhtar_token = _login(client, ids["mukhtar1_email"])
    resp = client.patch(
        f"/api/v1/population/change-requests/{cr_id}/review",
        json={"action": "reject"},
        headers=_auth_header(mukhtar_token),
    )
    assert resp.status_code == 400

    # With reason it succeeds.
    resp = client.patch(
        f"/api/v1/population/change-requests/{cr_id}/review",
        json={"action": "reject", "rejection_reason": "بيانات غير مكتملة"},
        headers=_auth_header(mukhtar_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == ChangeRequestStatus.rejected.value
    assert resp.json()["rejection_reason"] == "بيانات غير مكتملة"


def test_approved_request_cannot_be_approved_twice(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, head_token, ids["h1_id"], name="OnceOnly")

    chief_token = _login(client, ids["chief1_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/approve",
        json={},
        headers=_auth_header(chief_token),
    )
    assert resp.status_code == 200

    resp2 = client.post(
        f"/api/v1/population/change-requests/{cr_id}/approve",
        json={},
        headers=_auth_header(chief_token),
    )
    assert resp2.status_code == 400


def test_rejected_request_cannot_be_approved(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, head_token, ids["h1_id"])

    mukhtar_token = _login(client, ids["mukhtar1_email"])
    client.patch(
        f"/api/v1/population/change-requests/{cr_id}/review",
        json={"action": "reject", "rejection_reason": "مرفوض"},
        headers=_auth_header(mukhtar_token),
    )

    chief_token = _login(client, ids["chief1_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/approve",
        json={},
        headers=_auth_header(chief_token),
    )
    assert resp.status_code == 400


def test_duplicate_pending_birth_request_is_blocked(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    _submit_birth(client, head_token, ids["h1_id"], name="Twin1")
    # Second pending birth on the same household is blocked.
    resp = client.post(
        "/api/v1/population/change-requests",
        json={
            "request_type": "birth",
            "household_id": ids["h1_id"],
            "payload": {"full_name": "Twin2", "gender": "male"},
        },
        headers=_auth_header(head_token),
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------


def test_owner_can_cancel_pending_request(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, head_token, ids["h1_id"])

    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/cancel",
        headers=_auth_header(head_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == ChangeRequestStatus.cancelled.value


def test_non_owner_non_admin_cannot_cancel(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, head_token, ids["h1_id"])

    mukhtar_token = _login(client, ids["mukhtar1_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/cancel",
        headers=_auth_header(mukhtar_token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Audit + event log on every approval
# ---------------------------------------------------------------------------


def test_approval_writes_audit_and_event_log(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    cr_id = _submit_birth(client, head_token, ids["h1_id"], name="Logged")

    chief_token = _login(client, ids["chief1_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/approve",
        json={},
        headers=_auth_header(chief_token),
    )
    assert resp.status_code == 200

    with SessionLocal() as db:
        audit_rows = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == "population.change_request.approve",
                AuditLog.entity_id == str(cr_id),
            )
            .all()
        )
        assert len(audit_rows) == 1

        event_rows = (
            db.query(PopulationEventLog)
            .filter(
                PopulationEventLog.change_request_id == cr_id,
                PopulationEventLog.event_type == "change_request.approved",
            )
            .all()
        )
        assert len(event_rows) == 1
        # And a person.added event materialising the registry change.
        person_event = (
            db.query(PopulationEventLog)
            .filter(
                PopulationEventLog.change_request_id == cr_id,
                PopulationEventLog.event_type == "person.added",
            )
            .all()
        )
        assert len(person_event) == 1


# ---------------------------------------------------------------------------
# Listing + visibility
# ---------------------------------------------------------------------------


def test_household_head_only_sees_own_change_requests(client):
    ids = _seed_world()
    head1_token = _login(client, ids["head1_email"])
    head2_token = _login(client, ids["head2_email"])
    cr1 = _submit_birth(client, head1_token, ids["h1_id"], name="Baby1")
    cr2 = _submit_birth(client, head2_token, ids["h2_id"], name="Baby2")

    # head1 sees only their own request.
    resp = client.get(
        "/api/v1/population/change-requests", headers=_auth_header(head1_token)
    )
    assert resp.status_code == 200
    visible_ids = {r["id"] for r in resp.json()}
    assert cr1 in visible_ids
    assert cr2 not in visible_ids

    # And get-by-id of the other request is masked as 404.
    resp = client.get(
        f"/api/v1/population/change-requests/{cr2}",
        headers=_auth_header(head1_token),
    )
    assert resp.status_code == 404


def test_super_admin_sees_all_change_requests(client):
    ids = _seed_world()
    head1_token = _login(client, ids["head1_email"])
    head2_token = _login(client, ids["head2_email"])
    _submit_birth(client, head1_token, ids["h1_id"], name="A")
    _submit_birth(client, head2_token, ids["h2_id"], name="B")

    sa_token = _login(client, ids["sa_email"])
    resp = client.get(
        "/api/v1/population/change-requests", headers=_auth_header(sa_token)
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2
