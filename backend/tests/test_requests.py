from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.service import ServiceCatalogItem
from app.models.user import User, UserRole


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_create_request_and_update_status(client):
    with SessionLocal() as db:
        citizen = User(
            full_name="مواطن",
            email="citizen@example.com",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.citizen,
        )
        employee = User(
            full_name="موظف",
            email="employee@example.com",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.employee,
        )
        service = ServiceCatalogItem(code="SRV1", title_ar="خدمة", description_ar="وصف")
        db.add_all([citizen, employee, service])
        db.commit()

    citizen_token = _login(client, "citizen@example.com", "Passw0rd!")
    employee_token = _login(client, "employee@example.com", "Passw0rd!")

    create_resp = client.post(
        "/api/v1/requests",
        json={"service_id": 1, "title": "طلب جديد", "description": "تفاصيل الطلب"},
        headers=_auth_header(citizen_token),
    )
    assert create_resp.status_code == 201
    request_id = create_resp.json()["id"]

    status_resp = client.patch(
        f"/api/v1/requests/{request_id}/status",
        json={"new_status": "in_progress", "comment": "بدأت المعالجة"},
        headers=_auth_header(employee_token),
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["current_status"] == "in_progress"
