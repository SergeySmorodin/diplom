import os
import uuid

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import PermissionDenied

from cloud_app.models import File, Folder
from cloud_app.serializers import FileListSerializer, FileUploadSerializer, FileDeleteSerializer, FileRenameSerializer, \
    FileDownloadSerializer, FilePublicLinkSerializer, FileDownloadByLinkSerializer, \
    FolderWithFilesSerializer, FolderSerializer

User = get_user_model()


@pytest.mark.django_db
class TestFileListSerializer:
    def test_serializer_fields(self, test_file):
        serializer = FileListSerializer(test_file)
        data = serializer.data

        assert set(data.keys()) == {
            'id', 'original_name', 'size', 'upload_date',
            'last_download_date', 'comment', 'full_path',
            'file_url', 'public_link'
        }
        assert data['original_name'] == 'test.txt'
        assert isinstance(data['public_link'], str)


@pytest.mark.django_db
class TestFileUploadSerializer:

# fixme созданный каталог не удаляется из media
    def test_valid_upload(self, test_user, test_folder):
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("newfile.txt", file_content)

        data = {
            'file': uploaded_file,
            'comment': 'Test comment',
            'folder': test_folder.id
        }

        serializer = FileUploadSerializer(
            data=data,
            context={'request': type('Request', (), {'user': test_user})}
        )

        assert serializer.is_valid()
        file_instance = serializer.save()

        file_path = os.path.join(settings.MEDIA_ROOT, file_instance.file_path.name)
        assert os.path.exists(file_path)

        # Удаляем файл после теста
        if os.path.exists(file_path):
            os.remove(file_path)


    def test_invalid_folder_permission(self, other_user, test_user):
        other_folder = Folder.objects.create(
            name='Other Folder',
            owner=other_user
        )

        # Создаем загружаемый файл
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("newfile.txt", file_content)

        data = {
            'file': uploaded_file,
            'folder': other_folder.id
        }

        serializer = FileUploadSerializer(
            data=data,
            context={'request': type('Request', (), {'user': test_user})}
        )

        with pytest.raises(PermissionDenied) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "У вас нет прав на доступ к этой папке" in str(exc_info.value)

    def test_duplicate_filename(self, test_user, test_folder, test_file):
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content)

        data = {
            'file': uploaded_file,
            'folder': test_folder.id
        }

        serializer = FileUploadSerializer(
            data=data,
            context={'request': type('Request', (), {'user': test_user})}
        )

        assert not serializer.is_valid()
        assert 'file' in serializer.errors


@pytest.mark.django_db
class TestFileDeleteSerializer:
    def test_valid_delete(self, test_user, test_file):
        data = {
            'id': test_file.id
        }

        serializer = FileDeleteSerializer(
            data=data,
            context={'request': type('Request', (), {'user': test_user})}
        )

        assert serializer.is_valid()
        assert serializer.validated_data['id'] == test_file

    def test_invalid_owner(self, other_user, test_file):
        data = {
            'id': test_file.id
        }

        serializer = FileDeleteSerializer(
            data=data,
            context={'request': type('Request', (), {'user': other_user})}
        )

        with pytest.raises(PermissionDenied) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "Вы не можете удалить этот файл" in str(exc_info.value)


@pytest.mark.django_db
class TestFileRenameSerializer:
    def test_valid_rename(self, test_user, test_file):
        data = {
            'new_name': 'renamed.txt'
        }

        serializer = FileRenameSerializer(
            instance=test_file,
            data=data,
            context={'request': type('Request', (), {'user': test_user})}
        )

        assert serializer.is_valid()
        updated_file = serializer.save()
        assert updated_file.original_name == 'renamed.txt'

    def test_duplicate_name(self, test_user, test_folder):
        media_root = settings.MEDIA_ROOT
        os.makedirs(media_root, exist_ok=True)

        # Создаем временные файлы внутри MEDIA_ROOT
        file_path1 = os.path.join(media_root, "file1.txt")
        with open(file_path1, "wb") as f:
            f.write(b"Content of file1")

        file_path2 = os.path.join(media_root, "file2.txt")
        with open(file_path2, "wb") as f:
            f.write(b"Content of file2")

        file1 = File.objects.create(
            original_name="file1.txt",
            file_path=file_path1,
            size=100,
            owner=test_user,
            folder=test_folder
        )

        file2 = File.objects.create(
            original_name="file2.txt",
            file_path=file_path2,
            size=100,
            owner=test_user,
            folder=test_folder
        )

        data = {
            'new_name': 'file2.txt'
        }

        serializer = FileRenameSerializer(
            instance=file1,
            data=data,
            context={'request': type('Request', (), {'user': test_user})}
        )

        assert not serializer.is_valid()
        # Проверяем, что ошибка связана с полем 'new_name'
        assert 'new_name' in serializer.errors

        if os.path.exists(file_path1):
            os.remove(file_path1)
        if os.path.exists(file_path2):
            os.remove(file_path2)


@pytest.mark.django_db
class TestFileDownloadSerializer:
    def test_valid_download(self, test_user, test_file):
        assert test_file.last_download_date is None

        data = {
            'id': test_file.id
        }

        serializer = FileDownloadSerializer(
            data=data,
            context={'request': type('Request', (), {'user': test_user})}
        )

        assert serializer.is_valid()
        assert serializer.validated_data['id'] == test_file

        # Обновляем объект из базы данных
        test_file.refresh_from_db()
        # Проверяем, что last_download_date был обновлен
        assert test_file.last_download_date is not None


@pytest.mark.django_db
class TestFilePublicLinkSerializer:
    def test_generate_link(self, test_user, test_file):
        original_link = test_file.public_link

        serializer = FilePublicLinkSerializer(
            instance=test_file,
            data={},
            context={'request': type('Request', (), {'user': test_user})}
        )

        assert serializer.is_valid()
        updated_file = serializer.save()
        assert updated_file.public_link != original_link


@pytest.mark.django_db
class TestFileDownloadByLinkSerializer:
    def test_valid_download_by_link(self, test_file):
        data = {
            'public_link': test_file.public_link
        }

        serializer = FileDownloadByLinkSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == test_file

        test_file.refresh_from_db()
        assert test_file.last_download_date is not None

    def test_invalid_link(self):
        data = {
            'public_link': uuid.uuid4()
        }

        serializer = FileDownloadByLinkSerializer(data=data)
        assert not serializer.is_valid()
        assert 'public_link' in serializer.errors


@pytest.mark.django_db
class TestFolderSerializer:
    def test_create_folder(self, test_user):
        data = {
            'name': 'New Folder'
        }

        serializer = FolderSerializer(
            data=data,
            context={'request': type('Request', (), {'user': test_user})}
        )

        assert serializer.is_valid()
        folder = serializer.save()
        assert folder.owner == test_user
        assert folder.name == 'New Folder'


@pytest.mark.django_db
class TestFolderWithFilesSerializer:
    def test_serializer_with_files(self, test_user, test_folder, test_file):
        serializer = FolderWithFilesSerializer(test_folder)
        data = serializer.data

        assert 'files' in data
        assert 'children' in data
        assert len(data['files']) == 1
        assert data['files'][0]['original_name'] == 'test.txt'
