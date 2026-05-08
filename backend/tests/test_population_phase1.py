"""Phase-1 Population Registry coverage.

Complements `test_population.py` with the explicit RBAC matrix and
audit/event-log assertions called out in the Phase-1 spec.
"""

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.admin_scope import District, Governorate, Municipality, Neighborhood
from app.models.audit import AuditLog
from app.models.population import (
    Gender,
    Household,
    HouseholdVerificationStatus,
    Person,
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
    """Two-governorate world reused across Phase-1 tests."""
    with SessionLocal() as db:
        gov1 = Governorate(code="PG1", name_ar="غ1")
        gov2 = Governorate(code="PG2", name_ar="غ2")
        db.add_all([gov1, gov2])
        db.flush()

        mun1 = Municipality(governorate_id=gov1.id, code="PM1", name_ar="بلدية1")
        mun2 = Municipality(governorate_id=gov2.id, code="PM2", name_ar="بلدية2")
        db.add_all([mun1, mun2])
        db.flush()

        dist1 = District(municipality_id=mun1.id, code="PD1", name_ar="منطقة1")
        dist2 = District(municipality_id=mun2.id, code="PD2", name_ar="منطقة2")
        db.add_all([dist1, dist2])
        db.flush()

        nb1 = Neighborhood(district_id=dist1.id, code="PN1", name_ar="حي1")
        db.add(nb1)
        db.flush()

        users = {
            "sa": User(
                full_name="SA", email="p_sa@e.sy",
                password_hash=get_password_hash("Passw0rd!"),
                role=UserRole.super_admin,
            ),
            "gov1": User(
                full_name="Gov1", email="p_gov1@e.sy",
                password_hash=get_password_hash("Passw0rd!"),
                role=UserRole.governor, governorate_id=gov1.id,
            ),
            "chief1": User(
                full_name="Chief1", email="p_chief1@e.sy",
                password_hash=get_password_hash("Passw0rd!"),
                role=UserRole.municipality_chief,
                governorate_id=gov1.id, municipality_id=mun1.id,
            ),
            "chief2": User(
                full_name="Chief2", email="p_chief2@e.sy",
                password_hash=get_password_hash("Passw0rd!"),
                role=UserRole.municipality_chief,
                governorate_id=gov2.id, municipality_id=mun2.id,
            ),
            "mukhtar1": User(
                full_name="Mukhtar1", email="p_mukhtar1@e.sy",
                password_hash=get_password_hash("Passw0rd!"),
                role=UserRole.mukhtar,
                governorate_id=gov1.id, municipality_id=mun1.id,
                district_id=dist1.id, neighborhood_id=nb1.id,
            ),
            "head1": User(
                full_name="Head1", email="p_head1@e.sy",
                password_hash=get_password_hash("Passw0rd!"),
                role=UserRole.household_head,
            ),
            "head2": User(
                full_name="Head2", email="p_head2@e.sy",
                password_hash=get_password_hash("Passw0rd!"),
                role=UserRole.household_head,
            ),
            "citizen": User(
                full_name="Citizen", email="p_citizen@e.sy",
                password_hash=get_password_hash("Passw0rd!"),
                role=UserRole.citizen,
            ),
        }
        db.add_all(users.values())
        db.flush()

        h1 = Household(
            code="PH1", address_line="addr1",
            governorate_id=gov1.id, municipality_id=mun1.id,
            district_id=dist1.id, neighborhood_id=nb1.id,
            assigned_mukhtar_user_id=users["mukhtar1"].id,
            head_user_id=users["head1"].id,
            verification_status=HouseholdVerificationStatus.verified,
        )
        h2 = Household(
            code="PH2", address_line="addr2",
            governorate_id=gov2.id, municipality_id=mun2.id,
            district_id=dist2.id,
            head_user_id=users["head2"].id,
            verification_status=HouseholdVerificationStatus.pending,
        )
        db.add_all([h1, h2])
        db.flush()

        p1 = Person(
            household_id=h1.id, full_name="Head1 self",
            gender=Gender.male, relation_to_head=RelationToHead.self,
        )
        db.add(p1)
        db.commit()
        return {
            "h1_id": h1.id, "h2_id": h2.id,
            "gov1_id": gov1.id, "mun1_id": mun1.id,
            "dist1_id": dist1.id, "nb1_id": nb1.id,
            "emails": {k: v.email for k, v in users.items()},
        }


# ---------------------------------------------------------------------------
# Admin scopes
# ---------------------------------------------------------------------------


def test_admin_scopes_endpoint_returns_full_tree(client):
    ids = _seed_world()
    token = _login(client, ids["emails"]["sa"])
    resp = client.get("/api/v1/population/admin-scopes", headers=_auth_header(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert {g["code"] for g in body["governorates"]} == {"PG1", "PG2"}
    assert {m["code"] for m in body["municipalities"]} == {"PM1", "PM2"}
    assert {d["code"] for d in body["districts"]} == {"PD1", "PD2"}
    assert {n["code"] for n in body["neighborhoods"]} == {"PN1"}


def test_admin_scopes_requires_authentication(client):
    _seed_world()
    resp = client.get("/api/v1/population/admin-scopes")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Household visibility matrix
# ---------------------------------------------------------------------------


def test_municipality_chief_sees_only_own_municipality(client):
    ids = _seed_world()
    token = _login(client, ids["emails"]["chief1"])
    resp = client.get("/api/v1/population/households", headers=_auth_header(token))
    assert resp.status_code == 200
    codes = {h["code"] for h in resp.json()}
    assert codes == {"PH1"}

    # And cannot read a household outside their municipality.
    resp = client.get(
        f"/api/v1/population/households/{ids['h2_id']}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 404


def test_citizen_without_household_scope_cannot_access_households(client):
    ids = _seed_world()
    token = _login(client, ids["emails"]["citizen"])

    # Listing returns 403 — citizen is not a population reader.
    resp = client.get("/api/v1/population/households", headers=_auth_header(token))
    assert resp.status_code == 403

    # Direct lookup of any household is also denied.
    resp = client.get(
        f"/api/v1/population/households/{ids['h1_id']}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Nested person creation: audit + event logs
# ---------------------------------------------------------------------------


def test_household_head_can_add_person_via_nested_endpoint_with_logs(client):
    ids = _seed_world()
    token = _login(client, ids["emails"]["head1"])
    resp = client.post(
        f"/api/v1/population/households/{ids['h1_id']}/persons",
        json={
            "full_name": "New Child",
            "gender": "female",
            "relation_to_head": "child",
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    person_id = resp.json()["id"]
    assert resp.json()["household_id"] == ids["h1_id"]

    # Both an AuditLog row and a PopulationEventLog row must be written.
    with SessionLocal() as db:
        audit_rows = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == "population.person.create",
                AuditLog.entity_id == str(person_id),
            )
            .all()
        )
        assert len(audit_rows) == 1
        event_rows = (
            db.query(PopulationEventLog)
            .filter(
                PopulationEventLog.event_type == "person.created",
                PopulationEventLog.person_id == person_id,
            )
            .all()
        )
        assert len(event_rows) == 1
        assert event_rows[0].household_id == ids["h1_id"]


def test_nested_person_creation_denied_for_household_head_of_other_household(client):
    ids = _seed_world()
    token = _login(client, ids["emails"]["head1"])
    # head1 cannot add a person to head2's household (h2).
    resp = client.post(
        f"/api/v1/population/households/{ids['h2_id']}/persons",
        json={"full_name": "X", "gender": "male", "relation_to_head": "child"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 404  # masked as not-found per scope policy


def test_household_head_can_create_own_household_with_logs(client):
    ids = _seed_world()
    # head2 already has h2 — create a brand-new head user with no household.
    with SessionLocal() as db:
        new_head = User(
            full_name="Fresh Head",
            email="fresh_head@e.sy",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.household_head,
        )
        db.add(new_head)
        db.commit()
        new_head_id = new_head.id

    token = _login(client, "fresh_head@e.sy")
    resp = client.post(
        "/api/v1/population/households",
        json={
            "code": "PH-FRESH",
            "address_line": "fresh addr",
            "governorate_id": ids["gov1_id"],
            "municipality_id": ids["mun1_id"],
            "district_id": ids["dist1_id"],
            "neighborhood_id": ids["nb1_id"],
            # Even if the client supplies a different head_user_id, the
            # server must force it to current_user.id.
            "head_user_id": 99999,
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["head_user_id"] == new_head_id
    household_id = body["id"]

    with SessionLocal() as db:
        assert db.query(AuditLog).filter(
            AuditLog.action == "population.household.create",
            AuditLog.entity_id == str(household_id),
        ).count() == 1
        assert db.query(PopulationEventLog).filter(
            PopulationEventLog.event_type == "household.created",
            PopulationEventLog.household_id == household_id,
        ).count() == 1
