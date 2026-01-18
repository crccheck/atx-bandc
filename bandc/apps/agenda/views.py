from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.views.generic import DetailView, ListView

from .models import BandC, Document, Meeting


class BandCList(ListView):
    model = BandC

    def get_queryset(self):
        return super().get_queryset().select_related("latest_meeting")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["upcoming_meetings"] = (
            Meeting.objects.filter(date__gte=now().date())
            .select_related("bandc")
            .prefetch_related("documents")
            .order_by("date")
        )
        return data


class BandCDetail(ListView):
    template_name = "agenda/bandc_detail.html"
    paginate_by = 40

    def get_queryset(self, **kwargs):
        queryset = Document.objects.filter(active=True).select_related("meeting__bandc")

        if self.kwargs["slug"] == "all":
            self.bandc = None
        else:
            self.bandc = get_object_or_404(BandC, slug=self.kwargs["slug"])
            queryset = queryset.filter(meeting__bandc=self.bandc)

        # Get available years from Meeting table (more efficient than through Document)
        if self.bandc:
            meetings_qs = Meeting.objects.filter(bandc=self.bandc)
        else:
            meetings_qs = Meeting.objects.all()

        self.available_years = list(
            meetings_qs.values_list("date__year", flat=True)
            .distinct()
            .order_by("-date__year")
        )

        # Parse year parameter and filter
        year_param = self.request.GET.get("year")
        if year_param:
            try:
                self.selected_year = int(year_param)
            except ValueError:
                raise Http404("Invalid year")
            if self.selected_year not in self.available_years:
                raise Http404("Year not found")
        elif self.available_years:
            self.selected_year = self.available_years[0]  # Default to most recent
        else:
            self.selected_year = None

        if self.selected_year:
            queryset = queryset.filter(meeting__date__year=self.selected_year)

        return queryset

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["bandc"] = self.bandc
        data["available_years"] = self.available_years
        data["selected_year"] = self.selected_year
        if self.bandc:
            data["upcoming_meetings"] = Meeting.objects.filter(
                bandc=self.bandc,
                date__gte=now().date(),
            ).order_by("date")
        return data


class MeetingDetail(DetailView):
    model = Meeting

    def get_object(self, **kwargs):
        return get_object_or_404(
            self.model, bandc__slug=self.kwargs["bandc_slug"], date=self.kwargs["date"]
        )
