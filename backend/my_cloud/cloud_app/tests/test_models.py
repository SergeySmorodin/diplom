import os
import uuid
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from users.tests.factories import UserFactory
from ..models import Folder, File
from django.utils import timezone


@pytest.mark.django_db
class TestFolderModel:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = UserFactory()
        self.root_folder = Folder.objects.create(
            name='Root',
            owner=self.user,
            parent=None
        )
        self.child_folder = Folder.objects.create(
            name='Child',
            owner=self.user,
            parent=self.root_folder
        )

    def test_folder_creation(self):
        assert self.root_folder.name == 'Root'
        assert self.root_folder.owner == self.user
        assert self.root_folder.parent is None
        assert Folder.objects.filter(name='Root').exists()

    def test_child_folder_creation(self):
        assert self.child_folder.name == 'Child'
        assert self.child_folder.owner == self.user
        assert self.child_folder.parent == self.root_folder
        assert Folder.objects.filter(name='Child').exists()

    def test_get_folder_path_root(self):
        assert self.root_folder.get_folder_path() == ['Root']

    def test_get_folder_path_child(self):
        assert self.child_folder.get_folder_path() == ['Root', 'Child']

    def test_unique_together_constraint(self):
        with pytest.raises(Exception):
            Folder.objects.create(
                name='Child',
                owner=self.user,
                parent=self.root_folder
            )

    def test_str_representation(self):
        assert str(self.root_folder) == f'Root ({self.user})'


@pytest.mark.django_db
class TestFileModel:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = UserFactory()
        self.folder = Folder.objects.create(
            name='TestFolder',
            owner=self.user
        )
        self.sample_file = SimpleUploadedFile(
            'test_file.txt',
            b'Test file content'
        )
        self.file = File.objects.create(
            original_name='test_file.txt',
            size=self.sample_file.size,
            file_path=self.sample_file,
            owner=self.user,
            folder=self.folder
        )

    def test_file_creation(self):
        assert self.file.original_name == 'test_file.txt'
        assert self.file.owner == self.user
        assert self.file.folder == self.folder
        assert File.objects.filter(original_name='test_file.txt').exists()

    def test_file_size_auto_populated(self):
        new_file = File(
            original_name='new_file.txt',
            file_path=SimpleUploadedFile('new_file.txt', b'New content'),
            owner=self.user
        )
        new_file.save()
        assert new_file.size == len(b'New content')

    def test_update_download_date(self):
        old_date = self.file.last_download_date
        self.file.update_download_date()
        assert old_date != self.file.last_download_date
        assert pytest.approx(
            self.file.last_download_date.timestamp(),
            abs=1
        ) == timezone.now().timestamp()

    def test_get_full_path_with_folder(self):
        assert self.file.get_full_path() == 'TestFolder/test_file.txt'

    def test_get_full_path_without_folder(self):
        file_no_folder = File.objects.create(
            original_name='no_folder.txt',
            size=100,
            file_path=SimpleUploadedFile('no_folder.txt', b'No folder'),
            owner=self.user
        )
        assert file_no_folder.get_full_path() == 'no_folder.txt'

    def test_unique_constraint_per_folder(self):
        with pytest.raises(Exception):
            File.objects.create(
                original_name='test_file.txt',
                size=100,
                file_path=SimpleUploadedFile('test_file.txt', b'Duplicate'),
                owner=self.user,
                folder=self.folder
            )

    def test_public_link_auto_generated(self):
        assert isinstance(self.file.public_link, uuid.UUID)

    def test_str_representation(self):
        assert str(self.file) == f'test_file.txt ({self.user})'

    def teardown(self):
        if os.path.exists(self.file.file_path.path):
            os.remove(self.file.file_path.path)


@pytest.mark.django_db
class TestFolderFileIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = UserFactory()
        self.root = Folder.objects.create(
            name='Root',
            owner=self.user
        )
        self.subfolder = Folder.objects.create(
            name='Subfolder',
            owner=self.user,
            parent=self.root
        )
        self.file_in_root = File.objects.create(
            original_name='root_file.txt',
            size=10,
            file_path=SimpleUploadedFile('root_file.txt', b'Root file'),
            owner=self.user,
            folder=self.root
        )
        self.file_in_subfolder = File.objects.create(
            original_name='sub_file.txt',
            size=10,
            file_path=SimpleUploadedFile('sub_file.txt', b'Sub file'),
            owner=self.user,
            folder=self.subfolder
        )

    def test_file_path_generation_root(self):
        path = self.file_in_root.file_path.path
        assert str(self.user.id) in path
        assert 'Root' in path
        assert path.endswith('.txt')

    def test_file_path_generation_subfolder(self):
        path = self.file_in_subfolder.file_path.path
        assert str(self.user.id) in path
        assert 'Root' in path
        assert 'Subfolder' in path
        assert path.endswith('.txt')

    def test_folder_deletion_with_files(self):
        file_path = self.file_in_subfolder.file_path.path
        self.subfolder.delete()
        self.file_in_subfolder.refresh_from_db()
        assert self.file_in_subfolder.folder is None
        assert os.path.exists(file_path)

    def teardown(self):
        if hasattr(self, 'file_in_root') and os.path.exists(self.file_in_root.file_path.path):
            os.remove(self.file_in_root.file_path.path)
        if hasattr(self, 'file_in_subfolder') and os.path.exists(self.file_in_subfolder.file_path.path):
            os.remove(self.file_in_subfolder.file_path.path)