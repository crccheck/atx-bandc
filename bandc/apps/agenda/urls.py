from django.urls import path
from django.views.generic import DetailView

from .feeds import BandCDocumentFeed
from .models import Document, Meeting
from .views import BandCList, BandCDetail, MeetingDetail


urlpatterns = [
    path("", BandCList.as_view(), name="bandc_list"),
    path("<str:slug>/", BandCDetail.as_view(), name="bandc_detail"),
    path("feeds/<str:slug>/", BandCDocumentFeed(), name="feed"),
    path(
        "<str:bandc_slug>/<int:pk>/",
        DetailView.as_view(model=Document),
        name="document_detail",
    ),
    path(
        "<str:bandc_slug>/<int:edims_id>-<slug:fake_slug>/",
        DetailView.as_view(
            model=Document, slug_field="edims_id", slug_url_kwarg="edims_id"
        ),
        name="document_slug_detail",
    ),
    path(
        "<str:bandc_slug>/<str:date>/", MeetingDetail.as_view(), name="meeting_detail",
    ),
]
