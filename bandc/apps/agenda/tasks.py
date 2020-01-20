from .models import BandC, Document
from .pdf import process_pdf


def pull(bandc_pk: int):
    band = BandC.objects.get(pk=bandc_pk)
    band.pull()


def get_details_from_pdf(doc_pk: int):
    doc = Document.objects.get(pk=doc_pk)
    process_pdf(doc)
