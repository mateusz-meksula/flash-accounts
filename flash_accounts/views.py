from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status

from .serializers import UserCreateSerializer
from .settings import flash_settings
from .models import ActivationToken
from . import services


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
