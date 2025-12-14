import pytest


@pytest.mark.django_db
def test_logout(auth_client):
    login = auth_client.post("/api/auth/login/", {
        "email": "u@example.com",
        "password": "12345test"
    })

    refresh = login.data["refresh"]

    res = auth_client.post("/api/auth/logout/", {"refresh": refresh})
    assert res.status_code == 200


@pytest.mark.django_db
def test_logout_all(auth_client):
    res = auth_client.post("/api/auth/logout_all/")
    assert res.status_code in (200, 205)
    assert "detail" in res.data

@pytest.mark.django_db
def test_password_reset_request(api, user):
    res = api.post("/api/auth/password-reset/request/", {
        "email": user.email
    })
    assert res.status_code == 200

@pytest.mark.django_db
def test_password_reset_confirm(api, user):
    res = api.post("/api/auth/password-reset/confirm/", {
        "email": user.email,
        "token": "invalid-token",
        "new_password": "StrongPass123!",
    })

    assert res.status_code in (200, 400)

@pytest.mark.django_db
def test_password_reset_tokens(api, user):
    res = api.get("/api/auth/password-reset/tokens/")
    assert res.status_code in (200, 403, 401)

@pytest.mark.django_db
def test_login_wrong_password(api, user):
    res = api.post("/api/auth/login/", {
        "email": user.email,
        "password": "WRONGPASS"
    })

    assert res.status_code == 400 or res.status_code == 401
