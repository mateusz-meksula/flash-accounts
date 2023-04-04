from django.test import TestCase, SimpleTestCase
from django.contrib.auth import get_user_model
from .settings import flash_settings
from django.utils import timezone
from django.conf import settings

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
