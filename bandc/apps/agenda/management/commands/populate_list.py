from django.core.management.base import BaseCommand

from bandc.apps.agenda.models import BandC
from bandc.apps.agenda.utils import populate_bandc_list


class Command(BaseCommand):
    help = "Initialize or update the list of Boards and Commissions"

    def handle(self, *args, **options):
        self.stdout.write("Updating list of BandCs")
        populate_bandc_list()

        for bandc in BandC.objects.filter(active=True, identifier=None):
            self.stdout.write(f"Updating: {bandc}")
            bandc.pull_details()
