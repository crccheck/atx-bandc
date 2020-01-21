from django.core.management.base import BaseCommand

from bandc.apps.agenda.models import BandC, Document


class Command(BaseCommand):
    help = "Special version of 'scrape' for scraping one at a time in a cron job"

    def handle(self, *args, **options):
        queryset = BandC.objects.filter(scrapable=True).order_by("scraped_at")
        bandc = queryset[0]
        bandc.pull()
        self.stdout.write(self.style.SUCCESS(f'Scraped "{bandc}"'))

        qs = Document.objects.filter(page_count=None).exclude(thumbnail="")
        if qs.exists():
            doc = qs[0]
            doc.refresh()
            self.stdout.write(
                f'Re-scraped "{doc}" {doc.get_absolute_url()}, {qs.count()} left'
            )
        else:
            self.stdout.write(
                "No more missing Document.page_count we can delete the migration"
            )
