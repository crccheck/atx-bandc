from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(content_type="text/plain", template_name="robots.txt"),
    ),
    path("", include("bandc.apps.agenda.urls")),
]

if settings.DEBUG:
    urlpatterns.append(path("admin/", admin.site.urls))
