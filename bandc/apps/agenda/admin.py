from django.contrib import admin
from django.utils.html import format_html
from django_object_actions import DjangoObjectActions

from .models import BandC, Meeting, Document


@admin.register(BandC)
class BandCAdmin(admin.ModelAdmin):
    list_display = ("name", "scrapable", "identifier", "latest", "homepage_url")
    list_select_related = ("latest_meeting",)
    raw_id_fields = ("latest_meeting",)
    readonly_fields = ("scraped_at",)

    def latest(self, obj):
        if not obj.latest_meeting:
            return ""

        return obj.latest_meeting.date

    def homepage_url(self, obj: BandC):
        return format_html(
            f'<a href="{obj.homepage}" target="bandc">{obj.homepage.split("//")[1]}</a>'
        )


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "bandc")
    list_filter = ("bandc",)


@admin.register(Document)
class DocumentAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ("__str__", "edims_id", "date", "scrape_status")
    list_filter = ("scrape_status", "type")
    raw_id_fields = ("meeting",)

    def pdf(self, request, obj: Document):
        obj.refresh()

    objectactions = ("pdf",)
