# conftest.py

import pytest
from model_bakery import baker
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient
from django.conf import settings

@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def user():
    return baker.make(
        settings.AUTH_USER_MODEL,
        email="u@example.com",
        nickname="user1",
        is_active=True,
        password=make_password("12345test")
    )


@pytest.fixture
@pytest.mark.django_db
def auth_client(api, user):
    res = api.post("/api/auth/login/", {
        "email": "u@example.com",
        "password": "12345test"
    })

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    return api

