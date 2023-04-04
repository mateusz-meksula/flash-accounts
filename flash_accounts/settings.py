from django.core.signals import setting_changed
from django.utils import timezone
from django.conf import settings


DEFAULT_SETTINGS = {
    # account activation feature settings
    "ACTIVATE_ACCOUNT": True,
    "ACTIVATION_TOKEN_LIFETIME": timezone.timedelta(hours=1),
    "ACTIVATION_EMAIL_TEMPLATE": "empty for now",
    "ACTIVATION_EMAIL_SUBJECT": "empty for now",
    # password reset feature settings
    "PASSWORD_RESET_TOKEN_LIFETIME": timezone.timedelta(hours=1),
    "PASSWORD_RESET_EMAIL_TEMPLATE": "empty for now",
    "PASSWORD_RESET_EMAIL_SUBJECT": "empty for now",
    # email address, from which emails will appear to be sent
    "EMAIL_FROM": getattr(settings, "DEFAULT_EMAIL_FROM", "change@me.com"),
}


class FlashSettings:
    """
    Class for managing settings.
    
    Use user settings in priority,
    then default settings declared in `DEFAULT_SETTINGS` dict.
    """
    
    def __init__(self) -> None:
        self.default_settings = DEFAULT_SETTINGS
        self._loaded_settings = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self.__set_user_settings()
        return self._user_settings

    def __getattr__(self, attr):
        """
        Allows to access settings by attributes e.g: 
            `flash_settings.ACTIVATE_ACCOUNT`
        """

        # typos handling
        if attr not in self.default_settings:
            raise AttributeError(f"Unknown setting: {attr}")

        # first, check if user provided that setting
        # if not, load default value
        try:
            value = self.user_settings[attr]
        except KeyError:
            value = self.default_settings[attr]

        self._loaded_settings.add(attr)
        setattr(self, attr, value)

        return value

    def __set_user_settings(self):
        """
        Load user settings from main settings.
        """
        
        user_settings = getattr(settings, "FLASH_SETTINGS", {})
        self._user_settings = self.validate_user_settings(user_settings)

    def validate_user_settings(self, user_settings):
        """
        Basic validation of user settings.
        """
        
        # raise ValueError if provided setting is not defaults.
        unknown_settings = set(user_settings.keys() - self.default_settings.keys())
        if unknown_settings:
            raise ValueError(f"Unknown settings: {unknown_settings}")

        # raise TypeError if types does not match
        for key, value in user_settings.items():
            if type(self.default_settings[key]) != type(value):
                raise TypeError(f"{key} is not {type(self.default_settings[key])}")

        return user_settings

    def reload_settings(self):
        """
        Remove all attributes added by `__getattr__` method.
        """

        for attr in self._loaded_settings:
            delattr(self, attr)
        self._loaded_settings.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


flash_settings = FlashSettings()


def reload_settings(*args, **kwargs):
    """
    Call `reload_settings` method if user changed app settings.
    """

    if kwargs["setting"] == "FLASH_SETTINGS":
        flash_settings.reload_settings()


# signal
setting_changed.connect(reload_settings)