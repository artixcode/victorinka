import pytest

@pytest.mark.django_db
def test_register_and_login(api):
    res = api.post("/api/auth/register/", {"email": "new@ex.com", "password": "pass12345", "nickname": "A"}, format="json")
    assert res.status_code == 201
    res = api.post("/api/auth/login/", {"email": "new@ex.com", "password": "pass12345"}, format="json")
    assert res.status_code == 200
    assert "access" in res.data and "refresh" in res.data

@pytest.mark.django_db
def test_me_requires_auth(api):
    res = api.get("/api/auth/me/")
    assert res.status_code == 401

@pytest.mark.django_db
def test_me_with_auth(auth_client):
    res = auth_client.get("/api/auth/me/")
    assert res.status_code == 200
    assert "email" in res.data
