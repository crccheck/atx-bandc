from __future__ import unicode_literals

from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse

from .models import BandC, Document


class BandCDocumentFeed(Feed):
    description_template = 'agenda/document_description.html'

    def get_object(self, request, slug):
        if slug == 'all':
            return None

        return BandC.objects.get(slug=slug)

    def link(self, obj):
        return reverse('bandc:feed', kwargs={'slug': getattr(obj, 'slug', 'all')})

    def description(self, obj):
        if obj:
            return obj.description

        return 'Meeting activity of Austin Boards and Commissions.'

    def items(self, obj):
        queryset = Document.objects.filter(active=True).order_by('-meeting__date')
        if obj:
            queryset = queryset.filter(meeting__bandc=obj)
        return queryset[:50]

    def item_link(self, item):
        return item.url