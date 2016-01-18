from django.conf.urls import include, url
from django.contrib import admin
from bandc.apps.agenda.feeds import BandCDocumentFeed


urlpatterns = [
    url(r'^feeds/(?P<slug>[-\w]+)/$', BandCDocumentFeed(), name='bandc_feed'),

    url(r'^admin/', include(admin.site.urls)),
]
