from __future__ import unicode_literals

from django.contrib import admin
from django.utils.html import format_html
from django_object_actions import DjangoObjectActions

from .models import BandC, Meeting, Document
from .tasks import get_details_from_pdf


@admin.register(BandC)
class BandCAdmin(admin.ModelAdmin):
    list_display = ('name', 'scrapable', 'identifier', 'latest', 'homepage_url')
    list_select_related = ('latest_meeting', )
    raw_id_fields = ('latest_meeting', )

    def latest(self, obj):
        if not obj.latest_meeting:
            return ''

        return obj.latest_meeting.date

    def homepage_url(self, obj):
        return format_html('<a href="{}" target="bandc">{}</a>'.format(
            obj.homepage,
            obj.homepage.split('//')[1],  # don't show sceme to save space
        ))


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('bandc', 'date')
    list_filter = ('bandc', )


@admin.register(Document)
class DocumentAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('__unicode__', 'edims_id', 'date', 'scrape_status')
    list_filter = ('scrape_status', )
    raw_id_fields = ('meeting', )

    def pdf(self, request, obj):
        get_details_from_pdf.delay(obj.pk)

    objectactions = ('pdf', )
