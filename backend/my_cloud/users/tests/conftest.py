import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='Adminpass123!',
        is_admin=True,
        is_active=True,
        is_staff=True,
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username='regular',
        email='regular@example.com',
        password='Regularpass123!',
        is_active=True,
    )


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def authenticated_user_client(api_client, regular_user):
    api_client.force_authenticate(user=regular_user)
    return api_client
