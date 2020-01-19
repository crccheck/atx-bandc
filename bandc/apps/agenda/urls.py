from django.urls import path
from django.views.generic import DetailView

from .feeds import BandCDocumentFeed
from .models import Document
from .views import BandCList, BandCDetail


urlpatterns = [
    path("", BandCList.as_view(), name="bandc_list"),
    path("<str:slug>/", BandCDetail.as_view(), name="bandc_detail"),
    path("feeds/<str:slug>/", BandCDocumentFeed(), name="feed"),
    path(
        "<str:bandc_slug>/<int:pk>/",
        DetailView.as_view(model=Document),
        name="document_detail",
    ),
]
