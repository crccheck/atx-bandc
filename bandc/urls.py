from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import TemplateView


def favicon(request):
    """
    best by tezar tantular from the Noun Project
    """
    image_data = open("static/favicon.ico", "rb").read()
    return HttpResponse(image_data, content_type="image/x-icon")


urlpatterns = [
    path("favicon.ico", favicon),
    path(
        "robots.txt",
        TemplateView.as_view(content_type="text/plain", template_name="robots.txt"),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns.append(path("admin/", admin.site.urls))

urlpatterns.extend([path("", include("bandc.apps.agenda.urls"))])
