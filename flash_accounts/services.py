from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import ActivationToken, PasswordResetToken
from .settings import flash_settings


User = get_user_model()


def create_and_send_activation_token(user, request):
    """
    Generate email activation token and send email with activation link.
    """
    token = create_adequate_token(ActivationToken, user)
    url = build_url(request, "activate", token.token)

    send_mail_with_token(
        to_email=user.email,
        username=user.username,
        url=url,
        host=request.get_host(),
        template_name=flash_settings.ACTIVATION_EMAIL_TEMPLATE,
        subject=flash_settings.ACTIVATION_EMAIL_SUBJECT,
    )


def create_and_send_password_reset_token(user, request):
    """
    Generate password reset token and send email with instructions.
    """
    token = create_adequate_token(PasswordResetToken, user)
    url = build_url(request, "password_reset_confirm", token.token)

    send_mail_with_token(
        to_email=user.email,
        username=user.username,
        url=url,
        host=request.get_host(),
        template_name=flash_settings.PASSWORD_RESET_EMAIL_TEMPLATE,
        subject=flash_settings.PASSWORD_RESET_EMAIL_SUBJECT,
    )


def create_adequate_token(token_class_name, user):
    """
    Create and set-up given class name token.
    """
    token, _ = token_class_name.objects.get_or_create(user=user)
    token.set_up_token()
    token.save()
    return token


def build_url(request, url_name: str, token: str):
    """
    Make an url with token as a path parameter
    """
    url = f"{request.scheme}://{request.get_host()}"
    url += reverse(url_name, kwargs={"token_value": token})
    return url


def send_mail_with_token(to_email, username, url, host, template_name, subject):
    """
    Build mail from template and send to the user
    """
    from_email = flash_settings.EMAIL_FROM

    context = {
        "url": url,
        "username": username,
        "host": host,
    }

    html_content = render_to_string(f"{template_name}.html", context)
    text_content = render_to_string(f"{template_name}.txt", context)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
