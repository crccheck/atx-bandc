from django.contrib.syndication.views import Feed

from .models import BandC, Document


class BandCDocumentFeed(Feed):
    link = '/'  # TODO generate in def link(self, obj)
    description_template = 'agenda/document_description.html'

    def get_object(self, request, slug):
        if slug == 'all':
            return None

        return BandC.objects.get(slug=slug)

    def items(self, obj):
        queryset = Document.objects.filter(active=True).order_by('-meeting__date')
        if obj:
            queryset = queryset.filter(meeting__bandc=obj)
        return queryset[:30]

    def item_link(self, item):
        return item.url
