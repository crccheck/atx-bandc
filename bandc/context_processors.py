import os

from django.conf import settings


def base_url(request):
    return {
        "BASE_URL": os.getenv("BASE_URL")
        or request.build_absolute_uri("/").rstrip("/"),
        "RELEASE": settings.RELEASE,
    }
