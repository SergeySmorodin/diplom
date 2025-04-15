from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .factories import UserFactory

class LogoutViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()  
        self.url = reverse('logout')

    def test_logout_with_session_auth(self):
        self.assertTrue(
            self.client.login(username=self.user.username, password='testpass123'),
            "Пользователь должен успешно залогиниться"
        )
        
        response = self.client.post(self.url)
        
        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK,
            "Должен вернуться статус 200 после успешного выхода"
        )
        
        self.assertNotIn(
            '_auth_user_id', 
            self.client.session,
            "Идентификатор пользователя должен быть удален из сессии"
        )
        
        self.assertFalse(
            '_auth_user_id' in self.client.session,
            "Сессия должна быть очищена после выхода"
        )