from django.core.management.base import BaseCommand

from bandc.apps.agenda.models import BandC, Document


class Command(BaseCommand):
    help = "Special version of 'scrape' for scraping one at a time in a cron job"

    def handle(self, *args, **options):
        queryset = BandC.objects.filter(scrapable=True).order_by("scraped_at")
        bandc = queryset[0]
        bandc.pull()
        self.stdout.write(self.style.SUCCESS(f'Scraped "{bandc}"'))
