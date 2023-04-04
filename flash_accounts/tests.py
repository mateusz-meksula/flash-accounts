from django.test import SimpleTestCase
from .settings import flash_settings
from django.conf import settings

from .settings import settings as flash_settings_module


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
