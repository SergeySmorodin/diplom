import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from cloud_app.models import File, Folder


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user(db, django_user_model):
    """Фикстура для создания аутентифицированного пользователя"""
    user = django_user_model.objects.create_user(
        username='testuser',
        email='testuser@example.ru',
        password='Testpassword123!',
        is_active=True,
        # is_admin=True,
        # is_staff=True,
    )
    return user


@pytest.fixture
def folder(authenticated_user):
    """Фикстура для создания папки"""
    return Folder.objects.create(name="Test Folder", owner=authenticated_user)


@pytest.fixture
def file(authenticated_user, folder):
    """Фикстура для создания файла"""
    file_content = b"Test file content"
    uploaded_file = SimpleUploadedFile("test.txt", file_content)
    return File.objects.create(
        original_name="test.txt",
        file_path=uploaded_file,
        owner=authenticated_user,
        folder=folder
    )
