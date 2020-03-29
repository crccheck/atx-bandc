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
    yield _storage
    del _storage.bandcs
    del _storage.documents
    del _storage.meetings


@contextmanager
def record_scrape():
    """Create a `ScrapeLog` based on any scrapes that occur within"""
    with init() as context:
        yield
        log = ScrapeLog.objects.create(
            num_documents_found=len(context.documents), errors="TODO",
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
        # DELETEME, should skip if not initialized
        return

    _storage.documents.append((doc, created))
