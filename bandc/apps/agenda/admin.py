from django.contrib import admin
from django.utils.html import format_html
from django_object_actions import DjangoObjectActions

from .models import BandC, Meeting, Document


@admin.register(BandC)
class BandCAdmin(admin.ModelAdmin):
    list_display = ('name', 'scrapable', 'identifier', 'homepage_url')

    def homepage_url(self, obj):
        return format_html('<a href="{}" target="bandc">{}</a>'.format(
            obj.homepage,
            obj.homepage.split('//')[1],  # don't show sceme to save space
        ))


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('bandc', 'date')


@admin.register(Document)
class DocumentAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('__unicode__', 'edims_id', 'date')
    raw_id_fields = ('meeting', )

    def pdf(self, request, obj):
        from .pdf import process_pdf
        process_pdf(obj)

    objectactions = ('pdf', )
