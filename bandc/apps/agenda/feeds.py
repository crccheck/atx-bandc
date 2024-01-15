from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import BandC, Document

RSS_SIZE = 100


class BandCDocumentFeed(Feed):
    description_template = "agenda/document_description.html"

    def get_object(self, request, slug):
        self.slug = slug
        if slug == "all":
            return None

        return BandC.objects.get(slug=slug)

    def title(self, obj):
        return str(obj) if obj else "City of Austin Boards and Commissions - All"

    def link(self, obj):
        return reverse("feed", kwargs={"slug": getattr(obj, "slug", "all")})

    def description(self, obj):
        if obj:
            return obj.description

        return "Meeting activity of Austin Boards and Commissions."

    def items(self, obj):
        queryset = (
            Document.objects.filter(active=True)
            .select_related("meeting__bandc")
            .order_by("-scraped_at")
        )
        if obj:
            queryset = queryset.filter(meeting__bandc=obj)
        return queryset[:RSS_SIZE]

    def item_pubdate(self, item):
        return item.scraped_at

    def item_title(self, item):
        if self.slug == "all":
            return "{} - {}".format(item.meeting.bandc, item)

        return str(item)
