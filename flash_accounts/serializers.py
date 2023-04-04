from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

from rest_framework.validators import UniqueValidator, ValidationError
from rest_framework import serializers


User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for account creation.
    Checks for email uniqueness and requires to repeat password.
    """

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate(self, attrs):
        """
        Checks if user provided same password twice.
        """

        if attrs["password"] != attrs["password2"]:
            raise ValidationError({"password": "Provided passwords does not match."})
        attrs.pop("password2")
        return attrs
