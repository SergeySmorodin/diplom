import os
import uuid

import pytest
from django.urls import reverse

from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from rest_framework.exceptions import ErrorDetail
import urllib.parse
from cloud_app.models import File, Folder


def test_folder_creation(api_client, test_user):
    """Тест создания папки"""
    api_client.force_authenticate(user=test_user)
    url = reverse('cloud:folder-list')
    data = {'name': 'New Folder'}
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert Folder.objects.filter(name='New Folder', owner=test_user).exists()


def test_file_upload(api_client, test_user):
    """Тест загрузки файла"""
    # Проверяем доступность MEDIA_ROOT
    assert os.path.exists(settings.MEDIA_ROOT), f"MEDIA_ROOT {settings.MEDIA_ROOT} does not exist"
    assert os.access(settings.MEDIA_ROOT, os.W_OK), f"No write permissions for MEDIA_ROOT {settings.MEDIA_ROOT}"

    api_client.force_authenticate(user=test_user)
    url = reverse('cloud:file-upload')
    file_content = b"Test file content"
    uploaded_file = SimpleUploadedFile("test.txt", file_content)
    data = {'file': uploaded_file}

    try:
        response = api_client.post(url, data, format='multipart')
    except Exception as e:
        pytest.fail(f"Unexpected exception during file upload: {str(e)}")

    assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
        f"Server error: {response.data}"

    assert response.status_code == status.HTTP_201_CREATED, \
        f"Expected 201, got {response.status_code}. Response: {response.data}"

    assert File.objects.filter(original_name="test.txt", owner=test_user).exists(), \
        "File record was not created in database"


def test_file_upload_invalid_extension(api_client, test_user):
    """Тест загрузки файла с недопустимым расширением"""
    api_client.force_authenticate(user=test_user)
    url = reverse('cloud:file-upload')
    uploaded_file = SimpleUploadedFile("test.invalid", b"content")
    response = api_client.post(url, {'file': uploaded_file}, format='multipart')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'file' in response.data

    # Проверяем, что ошибка связана с полем 'file'
    error_detail = response.data['file'][0]
    assert isinstance(error_detail, ErrorDetail)
    assert str(error_detail) == 'Недопустимое расширение файла: .invalid'
    assert error_detail.code == 'invalid'


def test_file_list(api_client, test_user, test_folder, test_file):
    """Тест получения списка файлов"""
    api_client.force_authenticate(user=test_user)
    url = reverse('cloud:file-list') + f"?folder={test_folder.id}"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0


def test_file_download(api_client, test_user, test_file):
    """Тест скачивания файла"""
    api_client.force_authenticate(user=test_user)
    url = reverse('cloud:file-download', kwargs={'pk': test_file.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_filename = urllib.parse.quote(test_file.original_name)
    assert response['Content-Disposition'] == f'attachment; filename="{expected_filename}"'


def test_file_download_unauthorized(api_client, test_file):
    """Тест скачивания файла не аутентифицированным пользователем"""
    url = reverse('cloud-v1:file-download', kwargs={'pk': test_file.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_file_delete(api_client, test_user, test_file):
    """Тест удаления файла."""
    api_client.force_authenticate(user=test_user)
    url = reverse('cloud:file-delete', kwargs={'pk': test_file.id})
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not File.objects.filter(id=test_file.id).exists()


def test_file_rename(api_client, test_user, test_file):
    """Тест переименования файла"""
    api_client.force_authenticate(user=test_user)
    url = reverse('cloud:file-rename', kwargs={'pk': test_file.id})
    data = {'new_name': 'renamed.txt'}
    response = api_client.patch(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    test_file.refresh_from_db()
    assert test_file.original_name == 'renamed.txt'


def test_file_update_comment(api_client, test_user, test_file):
    """Тест обновления комментария к файлу"""
    api_client.force_authenticate(user=test_user)
    url = reverse('cloud:file-update-comment', kwargs={'pk': test_file.id})
    data = {'comment': 'New comment'}
    response = api_client.patch(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    test_file.refresh_from_db()
    assert test_file.comment == 'New comment'


def test_file_public_link(api_client, test_user, test_file):
    """Тест создания публичной ссылки на файл"""
    api_client.force_authenticate(user=test_user)
    url = reverse('cloud:file-public-link', kwargs={'pk': test_file.id})
    data = {'public_link': True}
    response = api_client.patch(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    test_file.refresh_from_db()

    # Проверяем, что public_link теперь содержит UUID
    assert test_file.public_link is not None
    assert isinstance(test_file.public_link, uuid.UUID)


def test_file_download_by_link(api_client, test_file):
    """Тест скачивания файла по публичной ссылке"""
    test_file.public_link = uuid.uuid4()
    test_file.save()

    url = reverse('cloud:file-download-by-link', kwargs={'public_link': test_file.public_link})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Disposition'] == f'attachment; filename="{test_file.original_name}"'

@pytest.mark.django_db
def test_file_download_by_link_invalid(api_client):
    """Тест скачивания файла по неверной публичной ссылке"""
    invalid_uuid = uuid.uuid4()
    url = reverse('cloud:file-download-by-link', kwargs={'public_link': invalid_uuid})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
