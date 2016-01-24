from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView


if settings.DEBUG:
    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),
    ]
else:
    urlpatterns = []

urlpatterns += [
    url(r'^robots.txt$', TemplateView.as_view(
        content_type='text/plain', template_name='robots.txt')),

    url(r'', include('bandc.apps.agenda.urls', namespace='bandc')),
]
