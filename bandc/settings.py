# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

import dj_database_url
from project_runpy import env

BASE_DIR = os.path.dirname(__file__)

SECRET_KEY = env.get("SECRET_KEY", "Rotom")
DEBUG = env.get("DEBUG", False)

ALLOWED_HOSTS = ["*"]


INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "bandc.apps.agenda",
    # support
    "django_extensions",
    "django_object_actions",
    "bootstrap_pagination",
)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

ROOT_URLCONF = "bandc.urls"

WSGI_APPLICATION = "bandc.wsgi.application"


# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

DATABASES = {"default": dj_database_url.config(default="sqlite:///bandc.db")}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/Chicago"

USE_I18N = False

USE_L10N = False

USE_TZ = True


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
        },
    },
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

MEDIA_ROOT = os.path.join(BASE_DIR, "..", "media")
MEDIA_URL = "/media/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": os.environ.get("LOG_LEVEL", "WARNING"), "handlers": ["console"]},
    "formatters": {
        "dev": {
            "format": "%(levelname)s %(name)s %(message)s",
            # 'datefmt': '%Y-%m-%dT%H:%M:%S%z',  # I want milliseconds but Python doesn't make it easy
            # "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
        "readable_sql": {"()": "project_runpy.ReadableSqlFilter"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "formatter": "dev",
            "class": "project_runpy.ColorizingStreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "level": "DEBUG" if env.get("SQL", False) else "INFO",
            "handlers": ["console"],
            "filters": ["require_debug_true", "readable_sql"],
            "propagate": False,
        },
        "sh": {"level": "WARNING", "propagate": False},
        "pdfminer": {"level": "WARNING", "propagate": False},
        "factory": {"level": "ERROR", "propagate": False},
    },
}
