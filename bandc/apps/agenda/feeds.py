from __future__ import unicode_literals

from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse

from .models import BandC, Document


class BandCDocumentFeed(Feed):
    description_template = 'agenda/document_description.html'

    def get_object(self, request, slug):
        self.slug = slug
        if slug == 'all':
            return None

        return BandC.objects.get(slug=slug)

    def title(self, obj):
        return unicode(obj) if obj else 'City of Austin Boards and Commissions - All'

    def link(self, obj):
        return reverse('bandc:feed', kwargs={'slug': getattr(obj, 'slug', 'all')})

    def description(self, obj):
        if obj:
            return obj.description

        return 'Meeting activity of Austin Boards and Commissions.'

    def items(self, obj):
        queryset = (
            Document.objects.filter(active=True)
            .select_related('meeting__bandc')
            .order_by('-scraped_at')
        )
        if obj:
            queryset = queryset.filter(meeting__bandc=obj)
        return queryset[:50]

    def item_pubdate(self, item):
        return item.scraped_at

    def item_title(self, item):
        if self.slug == 'all':
            return '{} - {}'.format(item.meeting.bandc, item)

        return unicode(item)
