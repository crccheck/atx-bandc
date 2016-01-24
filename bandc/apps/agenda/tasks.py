from celery import shared_task

from .models import BandC, Document
from .pdf import process_pdf


@shared_task
def pull(bandc_pk):
    band = BandC.objects.get(pk=bandc_pk)
    band.pull()


@shared_task
def get_details_from_pdf(doc_pk):
    doc = Document.objects.get(pk=doc_pk)
    process_pdf(doc)
