import pytest
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationView:
    def test_successful_registration(self, api_client):
        url = reverse('users:user-register')
        valid_data = {
            'username': 'newvaliduser',
            'email': 'newuser@example.com',
            'password': 'ValidPass123!',
        }
        response = api_client.post(url, valid_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['detail'] == 'User registered successfully'
        assert User.objects.filter(username='newvaliduser').exists()

    def test_registration_with_existing_username(self, api_client, regular_user):
        url = reverse('users:user-register')
        data = {
            'username': 'regular',  # уже существует
            'email': 'new@example.com',
            'password': 'ValidPass123!',
            'full_name': 'Иван Иванов'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data['errors']

    def test_registration_with_not_valid_passwords(self, api_client):
        url = reverse('users:user-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'notvalid',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data
        assert 'password' in response.data['errors']

    def test_registration_with_invalid_email(self, api_client):
        url = reverse('users:user-register')
        invalid_emails = [
            'plainstring',
            'missing@domain',
            '@missingusername.com',
            'invalid@.com'
        ]

        for email in invalid_emails:
            data = {
                'username': f'testuser_{email[:3]}',
                'email': email,
                'password': 'ValidPass123!',
                'full_name': 'Тест Пользователь'
            }
            response = api_client.post(url, data, format='json')

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'email' in response.data['errors']


@pytest.mark.django_db
class TestUserListView:
    def test_admin_can_list_users(self, authenticated_admin_client, regular_user):
        url = reverse('users:user-list')
        response = authenticated_admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # admin + regular user
        usernames = [user['username'] for user in response.data]
        assert 'regular' in usernames
        assert 'admin' in usernames

    def test_regular_user_cannot_list_users(self, authenticated_user_client):
        url = reverse('users:user-list')
        response = authenticated_user_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # fixme тут либо создать кастомный класс разрешений, либо с 403 сравнивать
    def test_unauthenticated_user_cannot_list_users(self, api_client):
        url = reverse('users:user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserDeleteView:
    def test_admin_can_delete_user(self, authenticated_admin_client, regular_user):
        url = reverse('users:user-delete', kwargs={'pk': regular_user.id})
        response = authenticated_admin_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'User deleted successfully'
        assert not User.objects.filter(id=regular_user.id).exists()

    def test_cannot_delete_self(self, authenticated_admin_client, admin_user):
        url = reverse('users:user-delete', kwargs={'pk': admin_user.id})
        response = authenticated_admin_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'Cannot delete yourself'
        assert User.objects.filter(id=admin_user.id).exists()

    def test_regular_user_cannot_delete(self, authenticated_user_client, regular_user):
        url = reverse('users:user-delete', kwargs={'pk': regular_user.id})
        response = authenticated_user_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestLoginView:
    def test_successful_login(self, api_client, regular_user):
        url = reverse('users:user-login')
        data = {
            'username': 'regular',
            'password': 'Regularpass123!'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Login successful'
        assert 'sessionid' in response.data
        assert response.data['user']['username'] == 'regular'

        session_key = response.data['sessionid']
        assert Session.objects.filter(session_key=session_key).exists()

    def test_invalid_credentials(self, api_client, regular_user):
        url = reverse('users:user-login')
        data = {
            'username': 'regular',
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['detail'] == 'Неверные имя пользователя или пароль'

    def test_validation_errors(self, api_client):
        url = reverse('users:user-login')
        data = {
            'username': '',
            'password': ''
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data
        assert 'username' in response.data['errors']
        assert 'password' in response.data['errors']


@pytest.mark.django_db
class TestLogoutView:
    def test_successful_logout(self, api_client, regular_user):

        login_url = reverse('users:user-login')
        login_data = {
            'username': 'regular',
            'password': 'Regularpass123!',
        }
        login_response = api_client.post(login_url, login_data, format='json')

        assert login_response.status_code == status.HTTP_200_OK
        assert 'sessionid' in login_response.data
        session_key = login_response.data['sessionid']

        # Тест выхода
        logout_url = reverse('users:user-logout')
        response = api_client.post(logout_url)

        # Проверяем успешный выход
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Logout successful'

        # Проверяем, что сессия удалена
        assert not Session.objects.filter(session_key=session_key).exists()

    def test_logout_unauthenticated(self, api_client):
        logout_url = reverse('users:user-logout')
        response = api_client.post(logout_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['detail'] == 'Not authenticated'
