import pytest
from rest_framework import status

class TestLoginAPI:
    def test_login_success(self, api_client, user):
        response = api_client.post(
            '/api/auth/login/',
            data={
                'username': user.username,
                'password': 'TestPass123!'
            },
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_login_failure(self, api_client, user):
        response = api_client.post(
            '/api/auth/login/',
            data={
                'username': user.username,
                'password': 'WrongPass123!'
            },
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST