from django.core.management.base import BaseCommand

from bandc.apps.agenda.models import Document


class Command(BaseCommand):
    help = "Special version of 'scrape' for re-scraping an old document"

    def handle(self, *args, **options):
        qs = Document.objects.filter(page_count=None).exclude(thumbnail="")
        if not qs.exists():
            self.stdout.write(
                "No more missing Document.page_count we can delete the migration"
            )

        for doc in qs:
            self.stdout.write(f"Examining {doc.scrape_status} {doc}...")
            doc.refresh()
            self.stdout.write(
                f'Re-scraped "{doc}" {doc.get_absolute_url()}, {qs.count()} left'
            )
            break
