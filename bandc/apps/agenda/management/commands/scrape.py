from django.core.management.base import BaseCommand, CommandError

from bandc.apps.agenda.models import BandC
from bandc.apps.agenda.utils import populate_bandc_list


class Command(BaseCommand):
    help = "Scrape meetings, optionally populate list of Boards and Commissions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--init-list",
            action="store_true",
            help="Initialize or update the list of BandCs.",
        )
        parser.add_argument(
            "identifier",
            nargs="*",
            help="Only scrape these identifiers (e.g.: 151 3 7)",
        )

    def handle(self, init_list, *args, **options):
        if init_list:
            self.stdout.write("Updating list of BandCs")
            populate_bandc_list()

            for bandc in BandC.objects.filter(identifier=None):
                self.stdout.write(f"Updating: {bandc}")
                bandc.pull_details()

        queryset = BandC.objects.filter(scrapable=True).order_by("?")
        if options["identifier"]:
            queryset = queryset.filter(identifier__in=options["identifier"])

        count = queryset.count()

        # TODO sort queryset
        # more frequently updated entries are first
        # prioritize buckets so defunct BandCs aren't scraped

        if count:
            self.stdout.write("Checking {} BandCs".format(queryset.count()))
        else:
            raise CommandError("No BandCs to scrape")

        for bandc in queryset:
            bandc.pull()
            self.stdout.write(self.style.SUCCESS(f'Scraped "{bandc}"'))
