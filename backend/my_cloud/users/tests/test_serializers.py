import pytest
from rest_framework.exceptions import ValidationError
from users.serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    UserLoginSerializer
)
from .factories import UserFactory
from django.utils.translation import gettext_lazy as _

@pytest.mark.django_db
class TestUserLoginSerializer:
    def test_valid_credentials(self):
        user = UserFactory.create(username='valid_user')
        user.set_password('correct_pass')
        user.save()        
        data = {
            'username': 'valid_user',
            'password': 'correct_pass'
        }
        serializer = UserLoginSerializer(data=data, context={'request': None})
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data['user'] == user

    def test_invalid_credentials(self):
        user = UserFactory.create(username='valid_user')
        user.set_password('correct_pass')
        user.save()        
        data = {
            'username': 'valid_user',
            'password': 'wrong_pass'
        }
        serializer = UserLoginSerializer(data=data, context={'request': None})
        with pytest.raises(ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        assert "Неверные имя пользователя или пароль" in str(excinfo.value.detail)

    def test_inactive_user(self):
        user = UserFactory.create(
            username='validuser1',
            is_active=False            
        )
        user.is_active = False
        user.save()     
        data = {
            'username': 'validuser1',
            'password': 'testpass123'
        }
        serializer = UserLoginSerializer(data=data, context={'request': None})
       
        assert not serializer.is_valid(), 'Ожидалась ошибка авторизации'
        expected_error_message = _('Аккаунт деактивирован')
        assert str(expected_error_message) in str(serializer.errors), f'Ошибка отличается от ожидаемой ({expected_error_message})'

    def test_password_input_type(self):
        serializer = UserLoginSerializer()
        assert serializer.fields['password'].style['input_type'] == 'password'

@pytest.mark.django_db
class TestUserRegistrationSerializer:
    def test_successful_registration(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'ValidPass123!',
            'full_name': 'New User'
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
        user = serializer.save()
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.check_password('ValidPass123!')
        assert user.full_name == 'New User'

    def test_duplicate_username(self):
        UserFactory.create(username='existing_user')
        data = {
            'username': 'existing_user',
            'email': 'new@example.com',
            'password': 'ValidPass123!',
            'full_name': 'Test User'
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors

    def test_duplicate_email(self):
        UserFactory.create(email='exist@example.com')
        data = {
            'username': 'testuser',
            'email': 'exist@example.com',
            'password': 'ValidPass123!',
            'full_name': 'Test User'
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_password_validation(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'short',
            'full_name': 'Test User'
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

@pytest.mark.django_db
class TestUserSerializer:
    def test_serialization(self):
        user = UserFactory.create(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            storage_path='/test/path',
            is_admin=False
        )
        
        serializer = UserSerializer(user)
        data = serializer.data
        
        expected_fields = {
            'id', 'username', 'email', 
            'full_name', 'is_admin', 'storage_path'
        }
        assert set(data.keys()) == expected_fields
        assert data['username'] == 'testuser'
        assert data['email'] == 'test@example.com'
        assert data['full_name'] == 'Test User'
        assert data['storage_path'] == '/test/path'
        assert data['is_admin'] is False

    def test_update(self):
        user = UserFactory.create(full_name='Old Name')
        serializer = UserSerializer(
            instance=user,
            data={'full_name': 'New Name'},
            partial=True
        )
        assert serializer.is_valid()
        updated_user = serializer.save()
        assert updated_user.full_name == 'New Name'