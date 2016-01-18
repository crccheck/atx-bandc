from django.core.management.base import BaseCommand, CommandError
from bandc.apps.agenda.models import BandC


class Command(BaseCommand):
    help = 'Scrape'

    def add_arguments(self, parser):
        parser.add_argument('identifier', nargs='+')

    def handle(self, *args, **options):
        queryset = BandC.objects.filter(scrapable=True)
        if options['identifier']:
            queryset = queryset.filter(identifier__in=options['identifier'])

        count = queryset.count()

        # TODO sort queryset
        # more frequently updated entries are first
        # priority buckets so defunct BandCs aren't scraped

        if count:
            self.stdout.write('count: {}'.format(queryset.count()))
        else:
            raise CommandError('No BandCs to scrape')

        for bandc in queryset:
            bandc.pull()
            self.stdout.write(self.style.SUCCESS('Scraped "%s"' % bandc))
