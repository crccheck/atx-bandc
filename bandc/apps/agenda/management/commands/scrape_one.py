import datetime as dt
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from bandc.apps.agenda import scrape_logger
from bandc.apps.agenda.models import BandC

# Boards with meetings within this window are considered "recently active"
RECENTLY_ACTIVE_THRESHOLD = timedelta(days=180)

# Target scrape intervals by activity level
RECENTLY_ACTIVE_INTERVAL = timedelta(hours=1)
NOT_RECENTLY_ACTIVE_INTERVAL = timedelta(hours=8)


def get_staleness_score(bandc: BandC, now: dt.datetime, today: dt.date) -> float:
    """
    Calculate how "overdue" a BandC is for scraping.

    Returns a ratio of (time_since_scraped / target_interval).
    Higher score = more urgently needs scraping.
    """
    is_recently_active = (
        bandc.latest_meeting
        and bandc.latest_meeting.date >= today - RECENTLY_ACTIVE_THRESHOLD
    )
    target_interval = (
        RECENTLY_ACTIVE_INTERVAL if is_recently_active else NOT_RECENTLY_ACTIVE_INTERVAL
    )

    if bandc.scraped_at is None:
        # Never scraped, highest priority
        return float("inf")

    time_since_scraped = now - bandc.scraped_at
    return time_since_scraped / target_interval


class Command(BaseCommand):
    help = "Special version of 'scrape' for scraping one at a time in a cron job"

    def handle(self, *args, **options) -> None:
        now = timezone.now()
        today = now.date()

        queryset = BandC.objects.filter(active=True, scrapable=True).select_related(
            "latest_meeting"
        )

        # Find the most overdue BandC based on activity-weighted staleness
        best_bandc: BandC | None = None
        best_score: float = -1
        for bandc in queryset:
            score = get_staleness_score(bandc, now, today)
            if score > best_score:
                best_score = score
                best_bandc = bandc

        if best_bandc is None:
            self.stdout.write(self.style.WARNING("No scrapable BandCs found"))
            return

        with scrape_logger.record_scrape():
            best_bandc.pull()

        self.stdout.write(self.style.SUCCESS(f'Scraped "{best_bandc}"'))
