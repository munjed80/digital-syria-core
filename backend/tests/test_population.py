"""Tests for the Population Registry: RBAC scoping and change-request workflow."""

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.admin_scope import District, Governorate, Municipality, Neighborhood
from app.models.population import (
    ChangeRequestStatus,
    Gender,
    Household,
    HouseholdVerificationStatus,
    Person,
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
    """Build a small two-governorate world and return its key objects."""
    with SessionLocal() as db:
        gov1 = Governorate(code="G1", name_ar="غ1")
        gov2 = Governorate(code="G2", name_ar="غ2")
        db.add_all([gov1, gov2])
        db.flush()

        mun1 = Municipality(governorate_id=gov1.id, code="M1", name_ar="بلدية1")
        mun2 = Municipality(governorate_id=gov2.id, code="M2", name_ar="بلدية2")
        db.add_all([mun1, mun2])
        db.flush()

        dist1 = District(municipality_id=mun1.id, code="D1", name_ar="منطقة1")
        dist2 = District(municipality_id=mun2.id, code="D2", name_ar="منطقة2")
        db.add_all([dist1, dist2])
        db.flush()

        nb1 = Neighborhood(district_id=dist1.id, code="N1", name_ar="حي1")
        db.add(nb1)
        db.flush()

        sa = User(
            full_name="SA", email="sa@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.super_admin,
        )
        gov1_user = User(
            full_name="Gov1", email="gov1@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.governor, governorate_id=gov1.id,
        )
        gov2_user = User(
            full_name="Gov2", email="gov2@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.governor, governorate_id=gov2.id,
        )
        chief1 = User(
            full_name="Chief1", email="chief1@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.municipality_chief,
            governorate_id=gov1.id, municipality_id=mun1.id,
        )
        mukhtar1 = User(
            full_name="Mukhtar1", email="mukhtar1@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.mukhtar,
            governorate_id=gov1.id, municipality_id=mun1.id,
            district_id=dist1.id, neighborhood_id=nb1.id,
        )
        head1 = User(
            full_name="Head1", email="head1@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.household_head,
        )
        head2 = User(
            full_name="Head2", email="head2@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.household_head,
        )
        db.add_all([sa, gov1_user, gov2_user, chief1, mukhtar1, head1, head2])
        db.flush()

        h1 = Household(
            code="H1", address_line="addr1",
            governorate_id=gov1.id, municipality_id=mun1.id,
            district_id=dist1.id, neighborhood_id=nb1.id,
            assigned_mukhtar_user_id=mukhtar1.id,
            head_user_id=head1.id,
            verification_status=HouseholdVerificationStatus.verified,
        )
        h2 = Household(
            code="H2", address_line="addr2",
            governorate_id=gov2.id, municipality_id=mun2.id,
            district_id=dist2.id,
            head_user_id=head2.id,
            verification_status=HouseholdVerificationStatus.pending,
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
            "mukhtar_email": mukhtar1.email,
            "chief_email": chief1.email,
            "gov1_email": gov1_user.email,
            "gov2_email": gov2_user.email,
            "sa_email": sa.email,
            "head1_email": head1.email,
            "head2_email": head2.email,
        }


def test_super_admin_sees_all_households(client):
    ids = _seed_world()
    token = _login(client, ids["sa_email"])
    resp = client.get("/api/v1/population/households", headers=_auth_header(token))
    assert resp.status_code == 200
    codes = {h["code"] for h in resp.json()}
    assert codes == {"H1", "H2"}


def test_governor_sees_only_own_governorate(client):
    ids = _seed_world()
    token = _login(client, ids["gov1_email"])
    resp = client.get("/api/v1/population/households", headers=_auth_header(token))
    assert resp.status_code == 200
    codes = {h["code"] for h in resp.json()}
    assert codes == {"H1"}


def test_mukhtar_sees_only_assigned_household(client):
    ids = _seed_world()
    token = _login(client, ids["mukhtar_email"])
    resp = client.get("/api/v1/population/households", headers=_auth_header(token))
    assert resp.status_code == 200
    codes = {h["code"] for h in resp.json()}
    assert codes == {"H1"}


def test_household_head_sees_only_own_household(client):
    ids = _seed_world()
    token = _login(client, ids["head1_email"])
    resp = client.get("/api/v1/population/households", headers=_auth_header(token))
    assert resp.status_code == 200
    codes = {h["code"] for h in resp.json()}
    assert codes == {"H1"}

    # And cannot read another household.
    resp = client.get(
        f"/api/v1/population/households/{ids['h2_id']}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 404


def test_household_head_cannot_create_person_directly(client):
    ids = _seed_world()
    token = _login(client, ids["head1_email"])
    resp = client.post(
        "/api/v1/population/persons",
        json={
            "household_id": ids["h1_id"],
            "full_name": "Forbidden Person",
            "gender": "male",
            "relation_to_head": "child",
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 403


def test_birth_change_request_flow(client):
    """Citizen submits a birth → mukhtar approves → registry updated."""
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    # Submit
    resp = client.post(
        "/api/v1/population/change-requests",
        json={
            "request_type": "birth",
            "household_id": ids["h1_id"],
            "payload": {
                "full_name": "Newborn",
                "gender": "female",
                "relation_to_head": "child",
                "birth_date": "2026-01-01",
            },
            "reason": "ولادة جديدة",
        },
        headers=_auth_header(head_token),
    )
    assert resp.status_code == 201, resp.text
    cr_id = resp.json()["id"]
    assert resp.json()["status"] == "mukhtar_review"

    # Mukhtar approves.
    mukhtar_token = _login(client, ids["mukhtar_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/mukhtar-decision",
        json={"approve": True, "comment": "تم التحقق"},
        headers=_auth_header(mukhtar_token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "approved"

    # The household now has a new member.
    resp = client.get(
        f"/api/v1/population/households/{ids['h1_id']}",
        headers=_auth_header(mukhtar_token),
    )
    assert resp.status_code == 200
    members = resp.json()["members"]
    assert any(m["full_name"] == "Newborn" for m in members)


def test_address_change_requires_municipality_review(client):
    """address_change is high-risk: mukhtar approval forwards to municipality."""
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    resp = client.post(
        "/api/v1/population/change-requests",
        json={
            "request_type": "address_change",
            "household_id": ids["h1_id"],
            "payload": {"address_line": "new addr"},
        },
        headers=_auth_header(head_token),
    )
    assert resp.status_code == 201
    cr_id = resp.json()["id"]

    mukhtar_token = _login(client, ids["mukhtar_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/mukhtar-decision",
        json={"approve": True},
        headers=_auth_header(mukhtar_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "municipality_review"

    # Mukhtar cannot finalise the high-risk change.
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/municipality-decision",
        json={"approve": True},
        headers=_auth_header(mukhtar_token),
    )
    assert resp.status_code == 403

    # Municipality chief approves.
    chief_token = _login(client, ids["chief_email"])
    resp = client.post(
        f"/api/v1/population/change-requests/{cr_id}/municipality-decision",
        json={"approve": True},
        headers=_auth_header(chief_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # Confirm address actually changed.
    resp = client.get(
        f"/api/v1/population/households/{ids['h1_id']}",
        headers=_auth_header(chief_token),
    )
    assert resp.status_code == 200
    assert resp.json()["address_line"] == "new addr"


def test_household_head_cannot_submit_for_other_household(client):
    ids = _seed_world()
    head_token = _login(client, ids["head1_email"])
    resp = client.post(
        "/api/v1/population/change-requests",
        json={
            "request_type": "birth",
            "household_id": ids["h2_id"],
            "payload": {"full_name": "X", "gender": "male"},
        },
        headers=_auth_header(head_token),
    )
    assert resp.status_code == 403


def test_statistics_scope_for_governor(client):
    ids = _seed_world()
    token = _login(client, ids["gov1_email"])
    resp = client.get("/api/v1/population/statistics", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    # Gov1 must only see H1 (one household, one person) — never H2.
    assert data["total_households"] == 1
    assert data["total_population"] == 1


def test_statistics_for_super_admin_includes_breakdown(client):
    ids = _seed_world()
    token = _login(client, ids["sa_email"])
    resp = client.get("/api/v1/population/statistics", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_households"] == 2
    assert len(data["administrative_breakdown"]) == 2
    # Pending vs verified counts.
    assert data["verified_households"] == 1
    assert data["pending_households"] == 1
