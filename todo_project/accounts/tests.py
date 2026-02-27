from django.urls import reverse
from django.test import TestCase

from .models import CustomUser


class LoginViewTests(TestCase):
    def setUp(self):
        self.username = 'tester'
        self.password = 'StrongPassword123!'
        CustomUser.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_login_missing_username_or_password_returns_error(self):
        response = self.client.post(reverse('login'), {'username': '', 'password': ''})

        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('required' in str(message).lower() for message in messages))

    def test_login_success_redirects_to_task_list(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password,
        })

        self.assertRedirects(response, reverse('task_list'))
