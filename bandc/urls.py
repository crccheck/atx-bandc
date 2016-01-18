from django.conf.urls import include, url
from django.contrib import admin
from bandc.apps.agenda.feeds import BandCDocumentFeed


urlpatterns = [
    url(r'^feeds/all/$', BandCDocumentFeed(), name='home'),

    url(r'^admin/', include(admin.site.urls)),
]
