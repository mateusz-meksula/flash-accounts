# <img src="./flash_accounts_header.jpg" alt="logo">

## **About**

Flash Accounts is a DRF lightweight reusable app for account management.  
It ships the following functionalities:

-   user registration,
-   user account activation,
-   password reset.

## **Requirements**

-   python >= 3.7
-   django >= 3.0
-   djangorestframework >= 3.11.0

## **Getting started**

### **Installation**

Flash Accounts can be installed with pip by running the following command:

```console
pip install flash-accounts
```

### **Configuration**

Add `flash_accounts` along `rest_framework` to `INSTALLED_APPS` in project's `settings.py` file:

```python
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "flash_accounts",
    # ...
]
```

Include Flash Accounts endpoints in project's `urls.py` file:

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path("api/auth/", include("flash_accounts.urls")),
    # ...
]
```

Configure an email backend. During development, you can use the console backend. Add the following line to the projects's `settings.py` file:

```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

**Note**: It is necessary to declare an email backend for Flash Accounts to work correctly.  
You can learn about Django email backends [here.](https://docs.djangoproject.com/en/4.2/topics/email/#email-backends)

<br>
Finally, run migrations by the following command:

```console
python manage.py migrate
```

**Note**: Flash Accounts migrations will create tables for `ActivationToken` and `PasswordResetToken` models.  
Flash Accounts do not provide custom user model, so you can (and should as it is explained [here](https://docs.djangoproject.com/en/4.1/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project)) set up your own.

## **Usage**

Flash accounts provide the following API endpoints:

```python
 - "/sign-up/"
 - "/account/activate/<str:token_value>/"
 - "/account/activate-resend/"
 - "/password-reset/"
 - "/password-reset/confirm/<str:token_value>/"
```

### <li><b> `/sign-up/` </b></li>

Allows user to create an account.

```python
URL: /sign-up/
HTTP METHOD: POST
HEADERS: {"Content-Type": "application/json"}
SUCCESS CODE: 201 Created

DATA FIELDS = "username", "email", "password", "password2"
```

Example:

```console
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "username": "user01",
        "email": "user01@user.com",
        "password": "userpassword123",
        "password2": "userpassword123"
    }' \
    http://localhost:8000/api/auth/sign-up/

{
    "email": "user01@user.com",
    "username": "user01"
}
```

### <li><b> `/account/activate/<str:token_value>/` </b></li>

Finds user model instance associated with `token_value` and sets its `is_active` attribute to `True`

```python
URL: /account/activate/<str:token_value>/
HTTP METHOD: GET
SUCCESS CODE: 200 OK
```

Example:

```console
curl -X GET \
    http://localhost:8000/api/auth/account/activate/x24qiuSIZx6badG0JdTxpih3pVyFlFb9JeW0Q3waEapeJR5fGnDyEVp/

{
    "account": "Account activated."
}
```

### <li><b> `/account/activate-resend/` </b></li>

Sends a new activation email, allowing users to activate account if previous token has expired.

```python
URL: /account/activate-resend/
HTTP METHOD: POST
HEADERS: {"Content-Type": "application/json"}
SUCCESS CODE: 200 OK

DATA FIELDS = "email"
```

Example:

```console
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"email": "user01@user.com"}' \
    http://localhost:8000/api/auth/account/activate-resend/

{
    "response": "Email with instructions has been sent to user01@user.com"
}
```

### <li><b> `/password-reset/` </b></li>

Sends email with password reset link.

```python
URL: /password-reset/
HTTP METHOD: POST
HEADERS: {"Content-Type": "application/json"}
SUCCESS CODE: 200 OK

DATA FIELDS = "email"
```

Example:

```console
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"email": "user01@user.com"}' \
    http://localhost:8000/api/auth/password-reset/

{
    "response": "Email with instructions has been sent to user01@user.com"
}
```

### <li><b> `/password-reset/confirm/<str:token_value>/` </b></li>

Finds user model instance associated with `token_value` and sets new password.

```python
URL: /password-reset/confirm/<str:token_value>/
HTTP METHOD: POST
HEADERS: {"Content-Type": "application/json"}
SUCCESS CODE: 200 OK

DATA FIELDS = "password", "password2"
```

Example:

```console
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "password": "NEWpassword123",
        "password2": "NEWpassword123"
    }' \
    http://localhost:8000/api/auth/password-reset/confirm/8kRuuRApqEQAeFeyzMSyAiYKtyT5DKEhrSkuSBcm3bmb4Gmih6DEVhr/

{
    "password": "Password has been changed."
}
```

## **Settings**

### **Default settings**

The default settings values are shown below:

```python
from django.utils import timezone
from django.conf import settings

DEFAULT_SETTINGS = {
    "ACTIVATE_ACCOUNT": True,
    "ACTIVATION_TOKEN_LIFETIME": timezone.timedelta(hours=1),
    "ACTIVATION_EMAIL_TEMPLATE": "flash_accounts/activate",
    "ACTIVATION_EMAIL_SUBJECT": "Activate your account.",
    "PASSWORD_RESET_TOKEN_LIFETIME": timezone.timedelta(hours=1),
    "PASSWORD_RESET_EMAIL_TEMPLATE": "flash_accounts/password_reset",
    "PASSWORD_RESET_EMAIL_SUBJECT": "Password reset request.",
    "EMAIL_FROM": getattr(settings, "DEFAULT_EMAIL_FROM", "change@me.com"),
}
```

#### <li><b> `ACTIVATE_ACCOUNT` </b></li>

When set to `True`, the registered account with the [`/sign-up/`](#sign-up) endpoint is created with the `is_active` field set to `False`, and an email with an activation link is sent to the user.  
When set to `False`, the registered account with the [`/sign-up/`](#sign-up) endpoint is created with the `is_active` field set to `True`, and no further actions are required. With that setting set to `False`, the following endpoints will not be available:

-   [`/account/activate/<str:token_value>/`](#accountactivatestrtoken_value)
-   [`/account/activate-resend/`](#accountactivate-resend)

#### <li><b> `ACTIVATION_TOKEN_LIFETIME` </b></li>

A `django.utils.timezone.timedelta` objects that determines how long the activation token remains valid.

#### <li><b> `ACTIVATION_EMAIL_TEMPLATE` </b></li>

Path to the activation email templates, **without** the file extension. This path points to two files:

-   activate.html
-   activate.txt

#### <li><b> `ACTIVATION_EMAIL_SUBJECT` </b></li>

Subject of activation email that is sent when new user registers.

#### <li><b> `PASSWORD_RESET_TOKEN_LIFETIME` </b></li>

A `django.utils.timezone.timedelta` objects that determines how long the password reset token is valid.

#### <li><b> `PASSWORD_RESET_EMAIL_TEMPLATE` </b></li>

Path to the password reset email templates, **without** the file extension. This path points to two files:

-   password_reset.html
-   password_reset.txt

#### <li><b> `PASSWORD_RESET_EMAIL_SUBJECT` </b></li>

Subject of password reset email that is sent when user requests password reset.

#### <li><b> `EMAIL_FROM` </b></li>

An email address from which emails will appear to be sent.  
Flash Accounts first checks if `DEFAULT_EMAIL_FROM` field is set in project's `settings.py` file.

### **Customizing settings**

Every setting value can be customized by creating a `FLASH_SETTINGS` dictionary in project's `settings.py` file.

Example:

```python
from django.utils import timezone

FLASH_SETTINGS = {
    "ACTIVATE_ACCOUNT": False,
    "PASSWORD_RESET_TOKEN_LIFETIME": timezone.timedelta(days=1),
    "EMAIL_FROM": "noreply@localhost.com",
}
```

#### **Overriding templates**

Email templates are located in `flash_accounts/templates/flash_accounts/` directory:

```
└── flash_accounts
    └── templates
        └── flash_accounts
            ├── activate.html
            ├── activate.txt
            ├── password_reset.html
            └── password_reset.txt
```

With that directory structure, the `APP_DIRS` setting value in the `TEMPLATES` section in project's `settings.py` must be set to `True`.  
If you want to provide your own email templates, you must place them in a valid Django templates directory.

Example:  
You can specify general templates directory:

```python
TEMPLATES = {
    # ...
    "DIRS": [BASE_DIR / "templates"],
    # ...
}
```

and put your templates in that directory:

```
└── drf_project
    ├── base
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── app_1
    ├── app_2
    ├── manage.py
    └── templates
        └── emails
            ├── custom_activation.html
            ├── custom_activation.txt
            ├── custom_password_reset.html
            └── custom_password_reset.txt
```

With that, you can specify the path to the templates:

```python
FLASH_SETTINGS = {
    # ...
    "ACTIVATION_EMAIL_TEMPLATE": "emails/custom_activation",
    "PASSWORD_RESET_EMAIL_TEMPLATE": "emails/custom_password_reset",
    # ...
}
```

It is nesseccary to include the `{{ url }}` Django template tag in your custom template files, so that emails will contain activation links or password reset links.  
Optional tags include `{{ username }}` and `{{ host }}`.

## **Upcoming features**

- Setting for switching off HTML email format.

## **Contributing**

If you find a bug, have a feature request, or want to help improve the project, please feel free to open an issue on this repository.

If you want to contribute to the project, please follow these guidelines:

1. Check for existing issues - Before opening a new issue, please check if someone else has already reported the same problem.

2. Describe the issue - When you open a new issue, please provide a clear description of the problem you're facing, including any error messages or steps to reproduce the problem.

3. Provide sample code - If you're reporting a bug or requesting a feature, please provide sample code that demonstrates the issue or the desired behavior.

4. Submit a pull request - If you want to contribute code changes, please fork the project and submit a pull request with your changes.

Thank you.
