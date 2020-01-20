import logging
import os
from io import StringIO
from urllib.request import urlretrieve

import sh
from django.core.files.base import ContentFile
from project_runpy import env
from pdfminer.converter import TextConverter
from pdfminer.pdfdocument import PDFDocument, PDFEncryptionError
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfparser import PDFParser
from pdfminer.psparser import PSException
from pdfminer.high_level import extract_text
from .models import Document


BASE_PATH = "/tmp/bandc_pdfs/"  # TODO settings
logger = logging.getLogger(__name__)


def pdf_file_path(document: Document) -> str:
    """
    Downloads the pdf locally and return the path it.

    We have to download the file to the disk because it's the easiest way to
    send the pdf to ImageMagick.
    """
    if not os.path.isdir(BASE_PATH):
        os.makedirs(BASE_PATH)

    filename = f"{document.edims_id}.pdf"
    tmp_filepath = os.path.join(BASE_PATH, f"{filename}.tmp")
    final_filepath = os.path.join(BASE_PATH, filename)
    logger.info(f"Downloading {document.date}: {document.url}")
    if not os.path.isfile(final_filepath):
        # WISHLIST stop using deprecated `urlretrieve`, add user-agent
        local_filename, headers = urlretrieve(document.url, tmp_filepath)
        logger.info("Downloaded to %s", local_filename)
        os.rename(local_filename, final_filepath)
    return final_filepath


def pdf_page_count(filepath: str) -> int:
    with open(filepath, "rb") as fp:
        return len(list(PDFPage.get_pages(fp, set())))


def grab_pdf_thumbnail(filepath: str) -> bytes:
    """
    Returns jpeg image thumbnail of the input pdf.
    """
    logger.info("Converting pdf: %s", filepath)
    out = sh.convert(
        filepath + "[0]",  # force to only get 1st page
        "-thumbnail",
        "400x400",  # output size
        "-flatten",
        "jpg:-",  # output jpeg to stdout
    )
    return out.stdout


def process_pdf(document: Document):
    if not document.edims_id:
        document.scrape_status = "unscrapable"
        document.save()
        return

    filepath = pdf_file_path(document)
    # Parse and save pdf text
    try:
        document.text = extract_text(filepath).strip()
        document.scrape_status = "scraped"
    except (
        PDFTextExtractionNotAllowed,
        PDFEncryptionError,
        PSException,
        # int() argument must be a string or a number, not 'PSKeyword'
        TypeError,
        # File "/usr/local/lib/python2.7/dist-packages/pdfminer/pdfpage.py", line 52, in __init__
        #     self.resources = resolve1(self.attrs['Resources'])
        # KeyError: 'Resources'
        KeyError,
        # File "/usr/local/lib/python2.7/site-packages/pdfminer/utils.py", line 46, in apply_png_predictor
        #   raise ValueError(ft)
        ValueError,
    ) as exc:
        document.text = ""
        document.scrape_status = "error"
        logger.error("PDF scrape error on EDIMS: %s Error: %s", document.edims_id, exc)

    thumbnail = grab_pdf_thumbnail(filepath)
    document.thumbnail.save(
        f"{document.edims_id}.jpg", ContentFile(thumbnail), save=False
    )
    document.save()
