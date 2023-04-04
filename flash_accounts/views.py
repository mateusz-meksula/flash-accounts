from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status

from .serializers import UserCreateSerializer, EmailSerializer, PasswordResetSerializer
from .models import ActivationToken, PasswordResetToken
from .settings import flash_settings
from . import services


User = get_user_model()


class UserCreateAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer

    # Account activation
    if flash_settings.ACTIVATE_ACCOUNT:

        def perform_create(self, serializer):
            """
            Save user account as inactive, create token and
            send mail with activation link.
            """

            user = serializer.save(is_active=False)
            services.create_and_send_activation_token(user, self.request)


@api_view(["GET"])
@permission_classes([AllowAny])
def activate_account(request, token_value):
    """
    Activate user account if activation token is valid.
    """

    token = get_object_or_404(ActivationToken, token=token_value)
    if token.expired:
        return Response(
            {"token": "token has expired."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Activate account and delete used token.
    user = token.user
    user.is_active = True
    user.save()
    token.delete()

    return Response({"account": "Account activated."}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Obtain email address, create password reset token
    and send email with instructions.
    """

    serializer = EmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.data["email"]
    user = get_object_or_404(User, email=email)

    services.create_and_send_password_reset_token(user, request)

    return Response(
        {"response": f"Email with instructions has been sent to {email}"},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def account_activation_resend(request):
    """
    Obtain email address, create activation token
    and send email with instructions.
    Check if user account is already activated.
    """

    serializer = EmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.data["email"]
    user = get_object_or_404(User, email=email)

    if user.is_active:
        return Response(
            {"account": "Account already activated."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    services.create_and_send_activation_token(user, request)
    return Response(
        {"response": f"Email with instructions has been sent to {email}"},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request, token_value):
    """
    Set new password if token and serializer data is valid.
    """

    serializer = PasswordResetSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = get_object_or_404(PasswordResetToken, token=token_value)
    if token.expired:
        return Response(
            {"token": "token has expired."}, status=status.HTTP_400_BAD_REQUEST
        )

    # set new password and delete used token.
    user = token.user
    new_password = serializer.validated_data["password"]
    user.set_password(new_password)
    user.save()
    token.delete()

    return Response(
        {"password": "Password has been changed."}, status=status.HTTP_200_OK
    )
