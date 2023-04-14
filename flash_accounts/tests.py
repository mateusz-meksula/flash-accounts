from django.test import TestCase, SimpleTestCase
from django.contrib.auth import get_user_model
from .settings import flash_settings
from django.template import loader
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.core import mail

from rest_framework.test import APITestCase
from rest_framework import status

from .settings import settings as flash_settings_module
from .models import ActivationToken, PasswordResetToken

import string


User = get_user_model()


class AppSettingsTestCase(SimpleTestCase):
    def test_loading_user_settings_correctly(self):
        user_settings = getattr(settings, "FLASH_SETTINGS", {})
        for setting, value in user_settings.items():
            self.assertEqual(value, getattr(flash_settings, setting))

    def test_loading_default_settings_correctly(self):
        default_settings = getattr(flash_settings_module, "DEFAULT_SETTINGS", {})
        user_settings = getattr(settings, "FLASH_SETTINGS", {})
        for setting, value in default_settings.items():
            if setting not in user_settings.keys():
                self.assertEqual(value, getattr(flash_settings, setting))


class ActivationTokenTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        self.user.save()
        self.token = ActivationToken.objects.create(user=self.user)
        self.characters = string.ascii_letters + string.digits

    def test_generate_token(self):
        self.assertEqual(self.token.token, "")

        self.token.generate_token()
        self.token.save()

        self.assertEquals(type(self.token.token), str)
        self.assertEqual(len(self.token.token), 55)

        for char in self.token.token:
            self.assertIn(char, self.characters)

    def test_set_expiration_date(self):
        self.assertEqual(self.token.expiration_date, None)

        self.token.set_expiration_date()
        self.token.save()

        self.assertLess(
            self.token.expiration_date,
            timezone.now()
            + flash_settings.ACTIVATION_TOKEN_LIFETIME
            + timezone.timedelta(seconds=10),
        )
        self.assertGreater(
            self.token.expiration_date,
            timezone.now()
            + flash_settings.ACTIVATION_TOKEN_LIFETIME
            - timezone.timedelta(seconds=10),
        )

    def test_expired_property_false(self):
        self.token.set_expiration_date()
        self.token.save()
        self.assertEqual(self.token.expired, False)

    def test_expired_property_true(self):
        self.token.expiration_date = timezone.now() - timezone.timedelta(seconds=5)
        self.token.save()
        self.assertEqual(self.token.expired, True)


class PasswordResetTokenTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        self.user.save()
        self.token = PasswordResetToken.objects.create(user=self.user)
        self.characters = string.ascii_letters + string.digits

    def test_generate_token(self):
        self.assertEqual(self.token.token, "")

        self.token.generate_token()
        self.token.save()

        self.assertEquals(type(self.token.token), str)
        self.assertEqual(len(self.token.token), 55)

        for char in self.token.token:
            self.assertIn(char, self.characters)

    def test_set_expiration_date(self):
        self.assertEqual(self.token.expiration_date, None)

        self.token.set_expiration_date()
        self.token.save()

        self.assertLess(
            self.token.expiration_date,
            timezone.now()
            + flash_settings.PASSWORD_RESET_TOKEN_LIFETIME
            + timezone.timedelta(seconds=10),
        )
        self.assertGreater(
            self.token.expiration_date,
            timezone.now()
            + flash_settings.PASSWORD_RESET_TOKEN_LIFETIME
            - timezone.timedelta(seconds=10),
        )

    def test_expired_property_false(self):
        self.token.set_expiration_date()
        self.token.save()
        self.assertEqual(self.token.expired, False)

    def test_expired_property_true(self):
        self.token.expiration_date = timezone.now() - timezone.timedelta(seconds=5)
        self.token.save()
        self.assertEqual(self.token.expired, True)


class RegisterTestCase(APITestCase):
    def setUp(self) -> None:
        self.valid_data = {
            "username": "testUser",
            "email": "testemail@test.com",
            "password": "testpassword123",
            "password2": "testpassword123",
        }
        self.invalid_passwords_data = {
            "username": "testUser",
            "email": "testemail@test.com",
            "password": "testpassword123",
            "password2": "testpassword321",
        }
        self.existing_email_data = {
            "username": "testUser2",
            "email": "testemail@test.com",
            "password": "test2password123",
            "password2": "test2password123",
        }
        self.existing_username_data = {
            "username": "testUser",
            "email": "testemail2@test.com",
            "password": "test2password123",
            "password2": "test2password123",
        }
        self.url = reverse("sign_up")

    def test_register_user(self):
        response = self.client.post(self.url, data=self.valid_data)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        u = User.objects.first()
        self.assertEqual(u.username, "testUser")
        self.assertEqual(u.email, "testemail@test.com")
        self.assertEqual(u.check_password("testpassword123"), True)

        if flash_settings.ACTIVATE_ACCOUNT:
            self.assertEqual(User.objects.first().is_active, False)
        else:
            self.assertEqual(User.objects.first().is_active, True)

    def test_register_user_invalid_data(self):
        response = self.client.post(self.url, data=self.invalid_passwords_data)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_email_exists(self):
        self.client.post(self.url, data=self.valid_data)
        response = self.client.post(self.url, data=self.existing_email_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_username_exists(self):
        self.client.post(self.url, data=self.valid_data)
        response = self.client.post(self.url, data=self.existing_username_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    if flash_settings.ACTIVATE_ACCOUNT:

        def test_email_token_generated(self):
            self.client.post(self.url, data=self.valid_data)

            token = ActivationToken.objects.first()

            self.assertEqual(ActivationToken.objects.count(), 1)
            self.assertEqual(token.user.username, "testUser")
            self.assertEqual(len(token.token), 55)
            self.assertLess(
                token.expiration_date,
                timezone.now()
                + flash_settings.ACTIVATION_TOKEN_LIFETIME
                + timezone.timedelta(seconds=10),
            )
            self.assertGreater(
                token.expiration_date,
                timezone.now()
                + flash_settings.ACTIVATION_TOKEN_LIFETIME
                - timezone.timedelta(seconds=10),
            )

        def test_activation_email_send(self):
            self.client.post(self.url, data=self.valid_data)
            self.assertEqual(len(mail.outbox), 1)

            token = ActivationToken.objects.first()

            url = "http://testserver"
            url += reverse("activate", kwargs={"token_value": token.token})
            context = {
                "url": url,
                "username": "testUser",
                "host": "testserver",
            }

            template_html = loader.render_to_string(
                f"{flash_settings.ACTIVATION_EMAIL_TEMPLATE}.html", context
            )
            template_txt = loader.render_to_string(
                f"{flash_settings.ACTIVATION_EMAIL_TEMPLATE}.txt", context
            )

            email_html = mail.outbox[0].alternatives[0][0]
            email_txt = mail.outbox[0].body

            self.assertEqual(template_html, email_html)
            self.assertEqual(template_txt, email_txt)


class PasswordResetTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        self.user.save()
        self.valid_data = {"email": "testemail@test.com"}
        self.invalid_data = {"email": "t35tem4il@test.com"}
        self.url = reverse("password_reset")

    def test_email_not_exist(self):
        response = self.client.post(self.url, data=self.invalid_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_email_not_provided(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_generated(self):
        self.client.post(self.url, data=self.valid_data)
        self.assertEqual(PasswordResetToken.objects.count(), 1)

        token = PasswordResetToken.objects.first()
        self.assertEqual(token.user.username, "testUser")
        self.assertEqual(len(token.token), 55)
        self.assertLess(
            token.expiration_date,
            timezone.now()
            + flash_settings.PASSWORD_RESET_TOKEN_LIFETIME
            + timezone.timedelta(seconds=10),
        )
        self.assertGreater(
            token.expiration_date,
            timezone.now()
            + flash_settings.PASSWORD_RESET_TOKEN_LIFETIME
            - timezone.timedelta(seconds=50),
        )

    def test_password_reset_token_regenerated(self):
        self.client.post(self.url, data=self.valid_data)
        token = PasswordResetToken.objects.first()
        old_expiration_date = timezone.now()
        token.expiration_date = old_expiration_date

        response = self.client.post(self.url, data=self.valid_data)
        token.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(token.expiration_date, old_expiration_date)
        self.assertGreater(token.expiration_date, old_expiration_date)

    def test_password_reset_email_sent(self):
        self.client.post(self.url, data=self.valid_data)
        self.assertEqual(len(mail.outbox), 1)

        token = PasswordResetToken.objects.first()

        url = "http://testserver"
        url += reverse("password_reset_confirm", kwargs={"token_value": token.token})
        context = {
            "url": url,
            "username": "testUser",
            "host": "testserver",
        }

        template_html = loader.render_to_string(
            f"{flash_settings.PASSWORD_RESET_EMAIL_TEMPLATE}.html",
            context,
        )
        template_txt = loader.render_to_string(
            f"{flash_settings.PASSWORD_RESET_EMAIL_TEMPLATE}.txt",
            context,
        )

        email_html = mail.outbox[0].alternatives[0][0]
        email_txt = mail.outbox[0].body

        self.assertEqual(template_html, email_html)
        self.assertEqual(template_txt, email_txt)


class PasswordResetConfirmTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        self.user.save()
        self.token = PasswordResetToken.objects.create(user=self.user)
        self.token.set_up_token()
        self.token.save()
        self.valid_data = {
            "password": "newtestpassWORD##1",
            "password2": "newtestpassWORD##1",
        }
        self.invalid_data = {
            "password": "newtestpassWORD##1",
            "password2": "newtestpassWORD@2",
        }
        self.valid_url = reverse(
            "password_reset_confirm", kwargs={"token_value": self.token.token}
        )
        self.invalid_url = reverse(
            "password_reset_confirm", kwargs={"token_value": "invalidTOKEN123"}
        )

    def test_request_with_invalid_passwords(self):
        response = self.client.post(self.valid_url, data=self.invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_token(self):
        self.valid_url = self.valid_url[:-56]
        response = self.client.post(self.valid_url, data=self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_token(self):
        response = self.client.post(self.invalid_url, data=self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_expired_token(self):
        self.token.expiration_date = timezone.now() - timezone.timedelta(seconds=5)
        self.token.save()
        url = reverse(
            "password_reset_confirm", kwargs={"token_value": self.token.token}
        )
        response = self.client.post(url, data=self.valid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"token": "token has expired."})

    def test_new_password_set_successfully(self):
        response = self.client.post(self.valid_url, data=self.valid_data)

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"password": "Password has been changed."})
        self.assertEqual(self.user.check_password("newtestpassWORD##1"), True)


if flash_settings.ACTIVATE_ACCOUNT:

    class ActivateAccountTestCase(APITestCase):
        def setUp(self) -> None:
            self.user = User.objects.create_user(
                username="testUser",
                email="testemail@test.com",
                password="testpassword123",
            )
            self.user.is_active = False
            self.user.save()
            self.token = ActivationToken.objects.create(user=self.user)
            self.token.set_up_token()
            self.token.save()
            self.valid_url = reverse(
                "activate", kwargs={"token_value": self.token.token}
            )
            self.invalid_url = reverse(
                "activate", kwargs={"token_value": "invalidTOKEN123"}
            )

        def test_valid_email_confirmation(self):
            self.assertEqual(User.objects.first().is_active, False)

            response = self.client.get(self.valid_url)

            self.user.refresh_from_db()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, {"account": "Account activated."})
            self.assertEqual(self.user.is_active, True)

        def test_url_missing_token(self):
            self.valid_url = self.valid_url[:-56]
            response = self.client.get(self.valid_url)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        def test_invalid_token(self):
            response = self.client.get(self.invalid_url)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        def test_expired_token(self):
            self.token.expiration_date = timezone.now() - timezone.timedelta(seconds=5)
            self.token.save()

            response = self.client.get(self.valid_url)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {"token": "token has expired."})

    class ActivateAccountResendTestCase(APITestCase):
        def setUp(self) -> None:
            self.inactive_user = User.objects.create_user(
                username="testUser",
                email="testemail@test.com",
                password="testpassword123",
                is_active=False,
            )
            self.inactive_user.save()
            self.active_user = User.objects.create_user(
                username="testActiveUser",
                email="testemailactive@test.com",
                password="testpassword123",
                is_active=True,
            )
            self.active_user.save()

            self.token = ActivationToken.objects.create(user=self.inactive_user)
            self.token.generate_token()
            self.old_expiration_date = timezone.now() - timezone.timedelta(seconds=10)
            self.token.expiration_date = self.old_expiration_date
            self.token.save()

            self.valid_data = {"email": "testemail@test.com"}
            self.invalid_data = {"email": "t35tem4il@test.com"}
            self.active_user_data = {"email": "testemailactive@test.com"}

            self.url = reverse("activate_resend")

        def test_email_not_exist(self):
            response = self.client.post(self.url, data=self.invalid_data)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        def test_email_not_provided(self):
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        def test_user_already_active(self):
            response = self.client.post(self.url, data=self.active_user_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {"account": "Account already activated."})

        def test_token_regenerated(self):
            response = self.client.post(self.url, data=self.valid_data)

            self.token.refresh_from_db()
            self.assertNotEqual(self.old_expiration_date, self.token.expiration_date)
            self.assertLess(
                self.token.expiration_date,
                timezone.now()
                + flash_settings.ACTIVATION_TOKEN_LIFETIME
                + timezone.timedelta(seconds=10),
            )
            self.assertGreater(
                self.token.expiration_date,
                timezone.now()
                + flash_settings.ACTIVATION_TOKEN_LIFETIME
                - timezone.timedelta(seconds=50),
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        def test_verification_email_sent(self):
            self.client.post(self.url, data=self.valid_data)
            self.assertEqual(len(mail.outbox), 1)
            self.token.refresh_from_db()

            url = "http://testserver"
            url += reverse("activate", kwargs={"token_value": self.token.token})
            context = {
                "url": url,
                "username": "testUser",
                "host": "testserver",
            }

            template_html = loader.render_to_string(
                f"{flash_settings.ACTIVATION_EMAIL_TEMPLATE}.html",
                context,
            )
            template_txt = loader.render_to_string(
                f"{flash_settings.ACTIVATION_EMAIL_TEMPLATE}.txt",
                context,
            )

            email_html = mail.outbox[0].alternatives[0][0]
            email_txt = mail.outbox[0].body

            self.assertEqual(template_html, email_html)
            self.assertEqual(template_txt, email_txt)
