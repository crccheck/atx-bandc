from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(content_type="text/plain", template_name="robots.txt"),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns.append(path("admin/", admin.site.urls))

urlpatterns.extend(
    [path("", include("bandc.apps.agenda.urls")),]
)
