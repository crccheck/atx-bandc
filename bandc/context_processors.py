import os


def base_url(request):
    return {
        "BASE_URL": os.getenv("BASE_URL")
        or request.build_absolute_uri("/").rstrip("/"),
    }
