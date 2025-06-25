import json
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from authenticate.views import RegisterView, LoginView, RefreshView, GetUser, LogoutView

class AuthenticationAPITests(APITestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_register_user_success(self):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'strongpassword123',
            'password2': 'strongpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.User.objects.filter(username='newuser').exists())
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertNotIn('password', response.data)

    def test_register_user_invalid_data(self):
        url = reverse('register')
        data = {
            'username': 'invaliduser',
            'email': 'invalid@example.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

        data = {
            'username': 'bademail',
            'email': 'bademail',
            'password': 'password123',
            'password2': 'password123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

        data = {
            'username': 'mismatch',
            'email': 'mismatch@example.com',
            'password': 'password123',
            'password2': 'password456'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_user_success(self):
        user = self.User.objects.create_user(
            username='loginuser', email='login@example.com', password='password123'
        )
        url = reverse('login')
        data = {
            'username': 'loginuser',
            'password': 'password123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh_token', response.cookies)
        self.assertIn('access_token', response.cookies)
        self.assertTrue(response.cookies['refresh_token']['httponly'])
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['secure'])
        self.assertTrue(response.cookies['access_token']['secure'])
        self.assertEqual(response.cookies['refresh_token']['samesite'], 'None')
        self.assertEqual(response.cookies['access_token']['samesite'], 'None')

    def test_login_user_invalid_credentials(self):
        self.User.objects.create_user(
            username='badloginuser', email='badlogin@example.com', password='password123'
        )
        url = reverse('login')
        data = {
            'username': 'badloginuser',
            'password': 'wrongpassword',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        data = {
            'username': 'nonexistentuser',
            'password': 'anypassword',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_authenticated(self):
        user = self.User.objects.create_user(
            username='getuser', email='get@example.com', password='password123'
        )
        self.client.force_authenticate(user=user)
        url = reverse('user')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'getuser')
        self.assertEqual(response.data['email'], 'get@example.com')

    def test_get_user_unauthenticated(self):
        url = reverse('user')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_user_success(self):
        user = self.User.objects.create_user(
            username='logoutuser', email='logout@example.com', password='password123'
        )
        login_url = reverse('login')
        login_data = {'username': 'logoutuser', 'password': 'password123'}
        self.client.post(login_url, login_data, format='json')

        logout_url = reverse('logout')
        response = self.client.post(logout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh_token', response.cookies)
        self.assertIn('access_token', response.cookies)
        self.assertEqual(response.cookies['refresh_token']['max_age'], 0)
        self.assertEqual(response.cookies['access_token']['max_age'], 0)

    def test_refresh_token_success(self):
        user = self.User.objects.create_user(
            username='refreshuser', email='refresh@example.com', password='password123'
        )
        login_url = reverse('login')
        login_data = {'username': 'refreshuser', 'password': 'password123'}
        login_response = self.client.post(login_url, login_data, format='json')

        refresh_token_value = login_response.cookies['refresh_token'].value
        access_token_value = login_response.cookies['access_token'].value

        refresh_url = reverse('refresh')
        self.client.cookies['refresh_token'] = refresh_token_value
        self.client.cookies['access_token'] = access_token_value

        response = self.client.post(refresh_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh_token', response.cookies)
        self.assertIn('access_token', response.cookies)
        self.assertNotEqual(response.cookies['refresh_token'].value, refresh_token_value)
        self.assertNotEqual(response.cookies['access_token'].value, access_token_value)

    def test_refresh_token_missing_token(self):
        url = reverse('refresh')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('refresh_token', response.cookies)
        self.assertEqual(response.cookies['refresh_token']['max_age'], 0)
