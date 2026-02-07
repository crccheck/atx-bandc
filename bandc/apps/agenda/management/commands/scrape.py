from django.core.management.base import BaseCommand, CommandError

from bandc.apps.agenda.models import BandC


class Command(BaseCommand):
    help = "Scrape meetings for Boards and Commissions"

    def add_arguments(self, parser):
        parser.add_argument(
            "identifier",
            nargs="*",
            help="Only scrape these identifiers (e.g.: 151 3 7)",
        )

    def handle(self, *args, **options):
        queryset = BandC.objects.filter(active=True, scrapable=True).order_by("?")
        if options["identifier"]:
            queryset = queryset.filter(identifier__in=options["identifier"])

        count = queryset.count()

        # TODO sort queryset
        # more frequently updated entries are first
        # prioritize buckets so defunct BandCs aren't scraped

        if count:
            self.stdout.write(f"Checking {queryset.count()} BandCs")
        else:
            raise CommandError("No BandCs to scrape")

        for bandc in queryset:
            self.stdout.write(f'Scraping "{bandc}" id #{bandc.identifier}')
            bandc.pull()
            self.stdout.write(self.style.SUCCESS(f' Scraped "{bandc}"'))
