import os

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from cloud_app.models import File, Folder

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    """Фикстура для создания аутентифицированного пользователя"""
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.ru',
        password='Testpassword123!',
        is_active=True,
    )
    yield user
    user.delete()


@pytest.fixture
def other_user(db):
    """Фикстура для создания другого пользователя"""
    user = User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='Otherpass123!'
    )
    yield user
    user.delete()


@pytest.fixture
def test_folder(test_user):
    """Фикстура для создания тестовой папки"""
    folder = Folder.objects.create(
        name='Test Folder',
        owner=test_user
    )
    yield folder
    folder.delete()


@pytest.fixture
def test_file(test_user, test_folder):
    file_content = b"Test file content"
    uploaded_file = SimpleUploadedFile("test.txt", file_content)
    file = File.objects.create(
        original_name="test.txt",
        file_path=uploaded_file,
        owner=test_user,
        folder=test_folder
    )
    yield file
    file.delete()
