from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.notification import Notification
from app.models.user import User, UserRole


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _seed_users_and_notifications():
    with SessionLocal() as db:
        citizen_a = User(
            full_name="مواطن أ",
            email="citizen_a@example.com",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.citizen,
        )
        citizen_b = User(
            full_name="مواطن ب",
            email="citizen_b@example.com",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.citizen,
        )
        employee = User(
            full_name="موظف",
            email="employee_n@example.com",
            password_hash=get_password_hash("Passw0rd!"),
            role=UserRole.employee,
        )
        db.add_all([citizen_a, citizen_b, employee])
        db.commit()
        db.add_all(
            [
                Notification(user_id=citizen_a.id, message="إشعار للمواطن أ #1"),
                Notification(user_id=citizen_a.id, message="إشعار للمواطن أ #2"),
                Notification(user_id=citizen_b.id, message="إشعار للمواطن ب"),
                Notification(user_id=employee.id, message="إشعار للموظف"),
            ]
        )
        db.commit()
        return citizen_a.id, citizen_b.id, employee.id


def test_list_notifications_returns_only_own(client):
    _seed_users_and_notifications()
    token = _login(client, "citizen_a@example.com", "Passw0rd!")

    resp = client.get("/api/v1/notifications", headers=_auth_header(token))
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert all(item["message"].startswith("إشعار للمواطن أ") for item in items)


def test_list_notifications_requires_auth(client):
    resp = client.get("/api/v1/notifications")
    assert resp.status_code == 401


def test_employee_sees_only_own_notifications(client):
    _seed_users_and_notifications()
    token = _login(client, "employee_n@example.com", "Passw0rd!")
    resp = client.get("/api/v1/notifications", headers=_auth_header(token))
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["message"] == "إشعار للموظف"


def test_mark_own_notification_read(client):
    _seed_users_and_notifications()
    token = _login(client, "citizen_a@example.com", "Passw0rd!")

    list_resp = client.get("/api/v1/notifications", headers=_auth_header(token))
    notif_id = list_resp.json()[0]["id"]

    patch_resp = client.patch(
        f"/api/v1/notifications/{notif_id}/read", headers=_auth_header(token)
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_read"] is True

    # Idempotent: a second call still returns 200 and is_read=True.
    patch_resp_2 = client.patch(
        f"/api/v1/notifications/{notif_id}/read", headers=_auth_header(token)
    )
    assert patch_resp_2.status_code == 200
    assert patch_resp_2.json()["is_read"] is True


def test_cannot_mark_other_users_notification_read(client):
    _seed_users_and_notifications()
    token_a = _login(client, "citizen_a@example.com", "Passw0rd!")
    token_b = _login(client, "citizen_b@example.com", "Passw0rd!")

    # Find citizen B's notification id while authenticated as B.
    list_resp = client.get("/api/v1/notifications", headers=_auth_header(token_b))
    other_id = list_resp.json()[0]["id"]

    # Citizen A must not be able to mark citizen B's notification as read.
    resp = client.patch(
        f"/api/v1/notifications/{other_id}/read", headers=_auth_header(token_a)
    )
    assert resp.status_code == 404


def test_mark_unknown_notification_returns_404(client):
    _seed_users_and_notifications()
    token = _login(client, "citizen_a@example.com", "Passw0rd!")
    resp = client.patch(
        "/api/v1/notifications/999999/read", headers=_auth_header(token)
    )
    assert resp.status_code == 404
