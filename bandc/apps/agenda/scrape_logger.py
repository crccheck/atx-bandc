import datetime as dt
import random
import threading
from contextlib import contextmanager
from datetime import timedelta

from django.utils import timezone

from .models import BandC, Document, Meeting, ScrapeLog

# For storing what happens during a scrape
# I probably don't need to be using thread storage
_storage = threading.local()


@contextmanager
def init():
    _storage.bandcs = []
    _storage.documents = []
    _storage.meetings = []
    _storage.errors = []
    yield _storage
    del _storage.bandcs
    del _storage.documents
    del _storage.meetings
    del _storage.errors


@contextmanager
def record_scrape():
    """
    Create a `ScrapeLog` based on any scrapes that occur within.

    Usage
    -----

    with record_scrape():
        # Your code here

    After your code executes, a `ScrapeLog` entry will be created. Any logs you
    create using .log_bandc, .log_meeting, etc will get added.
    """
    with init() as context:
        start = dt.datetime.now()
        yield
        log = ScrapeLog.objects.create(
            num_documents_found=len(context.documents),
            errors="\n".join(context.errors),
            duration=(dt.datetime.now() - start).microseconds / 1000,
        )
        log.bandcs_scraped.add(*context.bandcs)
        created_documents = [x[0] for x in context.documents if x[1]]
        log.documents_scraped.add(*created_documents)

        if random.random() < 0.1:
            cutoff_date = timezone.now() - timedelta(days=600)
            ScrapeLog.objects.filter(created__lt=cutoff_date).delete()


def log_bandc(bandc: BandC) -> None:
    """Log that a `BandC` was scraped"""
    if not hasattr(_storage, "bandcs"):
        return

    _storage.bandcs.append(bandc)


def log_meeting(meeting: Meeting, created: bool) -> None:
    if not hasattr(_storage, "meetings"):
        return

    _storage.meetings.append((meeting, created))


def log_document(doc: Document, created: bool) -> None:
    if not hasattr(_storage, "documents"):
        return

    _storage.documents.append((doc, created))


def error(message: str) -> None:
    if not hasattr(_storage, "errors"):
        return

    _storage.errors.append(message)
