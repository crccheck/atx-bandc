from django.conf.urls import url
from django.views.generic import DetailView, ListView

from .feeds import BandCDocumentFeed
from .models import BandC


urlpatterns = [
    url(r'^$', ListView.as_view(model=BandC), name='bandc_list'),
    url(r'^(?P<slug>[^/]+)/$', DetailView.as_view(model=BandC), name='bandc_detail'),
    url(r'^feeds/(?P<slug>[^/]+)/$', BandCDocumentFeed(), name='feed'),
]
