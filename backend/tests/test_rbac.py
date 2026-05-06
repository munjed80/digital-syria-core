from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_citizen_cannot_create_service(client):
    with SessionLocal() as db:
        citizen = User(
            full_name="مواطن",
            email="citizen2@example.com",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.citizen,
        )
        db.add(citizen)
        db.commit()

    token = _login(client, "citizen2@example.com", "Passw0rd!")

    response = client.post(
        "/api/v1/services",
        json={"code": "NEW_SERVICE", "title_ar": "خدمة جديدة", "description_ar": "وصف"},
        headers=_auth_header(token),
    )
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Insufficient role permissions"
