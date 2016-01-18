from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'', include('bandc.apps.agenda.urls', namespace='bandc')),

    url(r'^admin/', include(admin.site.urls)),
]
