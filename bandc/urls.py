from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin


if settings.DEBUG:
    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),
    ]
else:
    urlpatterns = []

urlpatterns += [
    url(r'', include('bandc.apps.agenda.urls', namespace='bandc')),
]
