def test_register_and_login(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "مستخدم تجريبي",
            "email": "citizen1@example.com",
            "password": "Passw0rd!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "citizen1@example.com", "password": "Passw0rd!"},
    )
    assert login_response.status_code == 200
    payload = login_response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"
