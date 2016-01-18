from django.views.generic import ListView
from django.shortcuts import get_object_or_404

from .models import BandC, Document


class BandCDetail(ListView):
    template_name = 'agenda/bandc_detail.html'

    def get_queryset(self, **kwargs):
        queryset = Document.objects.filter(active=True)

        if self.kwargs['slug'] == 'all':
            self.bandc = None
        else:
            self.bandc = get_object_or_404(BandC, slug=self.kwargs['slug'])
            queryset = queryset.filter(meeting__bandc=self.bandc)

        return queryset[:50]

    def get_context_data(self, **kwargs):
        data = super(BandCDetail, self).get_context_data(**kwargs)
        data['bandc'] = self.bandc
        return data
