from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models

from random import choice
import string

from .settings import flash_settings


User = get_user_model()


class BaseToken(models.Model):
    """
    Base class which token classes inherits from.
    """

    token = models.CharField(max_length=55)
    expiration_date = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def expired(self):
        """
        Returns `True` if token has expired.
        """

        return self.expiration_date < timezone.now()

    def generate_token(self):
        """
        Generates random, 55 characters long string.
        """

        characters = string.ascii_letters + string.digits
        self.token = "".join(choice(characters) for _ in range(55))

    def set_expiration_date(self):
        """
        Sets the expiration date for adequate token.
        """

        if self.__class__.__name__ == ActivationToken.__name__:
            token_lifetime = flash_settings.ACTIVATION_TOKEN_LIFETIME

        elif self.__class__.__name__ == PasswordResetToken.__name__:
            token_lifetime = flash_settings.PASSWORD_RESET_TOKEN_LIFETIME

        self.expiration_date = token_lifetime + timezone.now()

    def set_up_token(self):
        """
        Generate token and set expiration date.
        """

        self.generate_token()
        self.set_expiration_date()


class ActivationToken(BaseToken):
    """
    Token for account activation feature.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="activation_token"
    )


class PasswordResetToken(BaseToken):
    """
    Token for password reset feature.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="password_reset_token"
    )
