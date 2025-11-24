import pytest
from django.conf import settings
from rest_framework.test import APIClient
from model_bakery import baker

@pytest.fixture
def api():
    return APIClient()

@pytest.fixture
def user(db):
    return baker.make(settings.AUTH_USER_MODEL, email="u@example.com", nickname="user1", is_active=True, password=None)

@pytest.fixture
def user_with_password(db, django_user_model):
    user = django_user_model.objects.create_user(email="p@example.com", password="pass12345", nickname="puser")
    return user

@pytest.fixture
def auth_client(api, user_with_password):
    res = api.post("/api/auth/login/", {"email": "p@example.com", "password": "pass12345"}, format="json")
    assert res.status_code == 200, res.data
    token = res.data["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api

@pytest.fixture
def author(api, django_user_model):
    return django_user_model.objects.create_user(email="author@example.com", password="author12345", nickname="author")
