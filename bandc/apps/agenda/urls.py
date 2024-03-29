from django.urls import path, re_path
from django.views.generic import DetailView, ListView

from .feeds import BandCDocumentFeed
from .models import Document, ScrapeLog
from .views import BandCDetail, BandCList, MeetingDetail

urlpatterns = [
    path("", BandCList.as_view(), name="bandc_list"),
    path(
        "history/",
        ListView.as_view(
            queryset=ScrapeLog.objects.all().prefetch_related(
                "bandcs_scraped",
                "documents_scraped__meeting__bandc",
            ),
            ordering="-created",
            paginate_by=20,
        ),
        name="scrapelog_list",
    ),
    path("<str:slug>/", BandCDetail.as_view(), name="bandc_detail"),
    path("feeds/<str:slug>/", BandCDocumentFeed(), name="feed"),
    path(
        "<str:bandc_slug>/<int:pk>/",
        DetailView.as_view(model=Document),
        name="document_detail",
    ),
    re_path(
        r"^(?P<bandc_slug>[^/]+)/(?P<date>\d{4}-\d{2}-\d{2})/$",
        MeetingDetail.as_view(),
        name="meeting_detail",
    ),
    path(
        "<str:bandc_slug>/<int:edims_id>-<slug:fake_slug>/",
        DetailView.as_view(
            model=Document, slug_field="edims_id", slug_url_kwarg="edims_id"
        ),
        name="document_slug_detail",
    ),
]
