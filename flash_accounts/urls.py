from django.urls import path

from .settings import flash_settings
from . import views

# Registration
urlpatterns = [
    path("sign-up/", views.UserCreateAPIView.as_view(), name="sign_up"),
]

# Account activation
if flash_settings.ACTIVATE_ACCOUNT:
    urlpatterns += [
        path(
            "account/activate/<str:token_value>/",
            views.activate_account,
            name="activate",
        ),
    ]

# Password reset
urlpatterns += [
    path(
        "password-reset",
        views.password_reset_request,
        name="password_reset",
    ),
    path(
        "password-reset/confirm/<str:token_value>/",
        views.password_reset_confirm,
        name="password_reset_confirm",
    ),
]
