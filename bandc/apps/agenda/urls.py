from django.conf.urls import url
from django.views.generic import DetailView, ListView

from .feeds import BandCDocumentFeed
from .models import BandC
from .views import BandCDetail


urlpatterns = [
    url(r'^$', ListView.as_view(model=BandC), name='bandc_list'),
    url(r'^(?P<slug>[^/]+)/$', BandCDetail.as_view(), name='bandc_detail'),
    url(r'^feeds/(?P<slug>[^/]+)/$', BandCDocumentFeed(), name='feed'),
]
