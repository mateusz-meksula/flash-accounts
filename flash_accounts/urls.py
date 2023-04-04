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
