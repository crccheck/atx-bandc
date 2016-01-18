from django.conf.urls import url
from django.views.generic import ListView

from .feeds import BandCDocumentFeed
from .models import BandC


urlpatterns = [
    url(r'^$', ListView.as_view(model=BandC), name='bandc_list'),
    url(r'^feeds/(?P<slug>[^/]+)/$', BandCDocumentFeed(), name='feed'),
]
