from django.contrib.syndication.views import Feed

from .models import Document


class BandCDocumentFeed(Feed):
    link = '/'
    description_template = 'agenda/document_description.html'

    def items(self):
        return Document.objects.order_by('-meeting__date')[:30]

    def item_link(self, item):
        return item.url
