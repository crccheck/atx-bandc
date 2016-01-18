from django.conf.urls import url
from .feeds import BandCDocumentFeed


urlpatterns = [
    url(r'^feeds/(?P<slug>[-\w]+)/$', BandCDocumentFeed(), name='feed'),
]
