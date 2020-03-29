import datetime as dt
import threading
from contextlib import contextmanager

from .models import BandC, Document, Meeting, ScrapeLog

# For storing what happens during a scrape
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
    """Create a `ScrapeLog` based on any scrapes that occur within"""
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


def log_bandc(bandc: BandC):
    """Log that a `BandC` was scraped"""
    if not hasattr(_storage, "bandcs"):
        return

    _storage.bandcs.append((bandc))


def log_meeting(meeting: Meeting, created: bool):
    if not hasattr(_storage, "meetings"):
        return

    _storage.meetings.append((meeting, created))


def log_document(doc: Document, created: bool):
    if not hasattr(_storage, "documents"):
        return

    _storage.documents.append((doc, created))


def error(message: str):
    if not hasattr(_storage, "errors"):
        return

    _storage.errors.append(message)
