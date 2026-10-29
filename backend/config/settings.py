"""Django settings for the Activity Pulse API.

Deliberately minimal: a read-only JSON API over one domain app. Authentication,
admin, sessions, templates and static files are out of scope for this exercise.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Local development only. Override both before any real deployment.
SECRET_KEY = "django-insecure-local-development-only"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "drf_spectacular",
    "activity",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# Templates are only needed for the Swagger UI page served by drf-spectacular.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
    }
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Timestamps are stored in UTC; each account's own timezone is applied in the service layer.
USE_TZ = True
TIME_ZONE = "UTC"
USE_I18N = False

# Read-only JSON API, no authentication. Without auth/sessions installed, DRF's default
# authentication classes must be disabled.
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Activity Pulse API",
    "DESCRIPTION": (
        "Read-only API for DASH-247: compares a customer's last complete local week of activity with "
        "its recent history, per location. No authentication."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Swagger UI assets come from a CDN; pinned so the page does not change under us.
    "SWAGGER_UI_DIST": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14",
    "SWAGGER_UI_SETTINGS": {"defaultModelsExpandDepth": 1, "tryItOutEnabled": True},
}
