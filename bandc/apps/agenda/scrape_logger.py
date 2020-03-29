import threading
from contextlib import contextmanager

from .models import Document, Meeting

# For storing what happens during a scrape
_storage = threading.local()


@contextmanager
def init():
    _storage.documents = []
    _storage.meetings = []
    yield _storage
    del _storage.documents
    del _storage.meetings


def log_meeting(meeting: Meeting, created: bool):
    if not hasattr(_storage, "meetings"):
        return

    _storage.meetings.append((meeting, created))
    print(_storage.meetings)


def log_document(doc: Document, created: bool):
    if not hasattr(_storage, "documents"):
        # DELETEME, should skip if not initialized
        return

    _storage.documents.append((doc, created))
    print(_storage.documents)
