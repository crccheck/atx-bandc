from django.contrib import admin
from django.utils.html import format_html

from .models import Year, BandC


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    pass


@admin.register(BandC)
class BandCAdmin(admin.ModelAdmin):
    list_display = ('name', 'scrapable', 'identifier', 'homepage_url')

    def homepage_url(self, obj):
        return format_html('<a href="{}" target="bandc">{}</a>'.format(
            obj.homepage,
            obj.homepage.split('//')[1],  # don't show sceme to save space
        ))
