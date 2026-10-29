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
    "activity",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
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
