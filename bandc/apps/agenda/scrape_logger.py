import threading

from .models import Document

# For storing what happens during a scrape
scrape_storage = threading.local()


def init_storage():
    scrape_storage.documents = []


def log_document(doc: Document, created: bool):
    if not hasattr(scrape_storage, "documents"):
        # DELETEME, should skip if not initialized
        init_storage()

    scrape_storage.documents.append((doc, created))
    print(scrape_storage.documents)