from django.conf.urls import url
from django.views.generic import DetailView

from .feeds import BandCDocumentFeed
from .models import Document
from .views import BandCList, BandCDetail


urlpatterns = [
    url(r'^$', BandCList.as_view(), name='bandc_list'),
    url(r'^(?P<slug>[^/]+)/$', BandCDetail.as_view(), name='bandc_detail'),
    url(r'^feeds/(?P<slug>[^/]+)/$', BandCDocumentFeed(), name='feed'),
    url(r'^(?P<bandc_slug>[^/]+)/(?P<pk>\d+)/$',
        DetailView.as_view(model=Document),
        name='document_detail'),
]
