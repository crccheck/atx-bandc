from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.views.generic import DetailView, ListView

from .models import BandC, Meeting, Document


class BandCList(ListView):
    model = BandC

    def get_queryset(self):
        return super(BandCList, self).get_queryset().select_related("latest_meeting")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["upcoming_meetings"] = Meeting.objects.filter(date__gt=now()).order_by(
            "date"
        )
        return data


class BandCDetail(ListView):
    template_name = "agenda/bandc_detail.html"
    paginate_by = 20

    def get_queryset(self, **kwargs):
        queryset = Document.objects.filter(active=True).select_related("meeting__bandc")

        if self.kwargs["slug"] == "all":
            self.bandc = None
        else:
            self.bandc = get_object_or_404(BandC, slug=self.kwargs["slug"])
            queryset = queryset.filter(meeting__bandc=self.bandc)

        return queryset

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["bandc"] = self.bandc
        return data


class MeetingDetail(DetailView):
    model = Meeting

    def get_object(self, **kwargs):
        return get_object_or_404(
            self.model, bandc__slug=self.kwargs["bandc_slug"], date=self.kwargs["date"]
        )

