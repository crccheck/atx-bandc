from django.contrib import admin
from .models import Year, BandC


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    pass


@admin.register(BandC)
class BandCAdmin(admin.ModelAdmin):
    list_display = ('name', 'homepage')
