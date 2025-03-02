import logging
import os
from io import StringIO
from pathlib import Path
from urllib.request import urlretrieve
from pathlib import Path

from django.core.files.base import ContentFile
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFEncryptionError
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.psparser import PSException
from sh import convert

from .models import Document

BASE_PATH = "/tmp/bandc_pdfs/"  # TODO settings
logger = logging.getLogger(__name__)


def extract_text(
    pdf_file,
    password="",
    page_numbers=None,
    maxpages=0,
    caching=True,
    codec="utf-8",
    laparams=None,
    check_extractable=True,
) -> str:
    """Parse and return the text contained in a PDF file.

    Forked version of
    https://github.com/pdfminer/pdfminer.six/blob/52da65d5eb0e8ca85a66dc728f06589ea160e172/pdfminer/high_level.py#L90-L91
    to fix: https://github.com/pdfminer/pdfminer.six/issues/350
    """
    if laparams is None:
        laparams = LAParams()

    with open(pdf_file, "rb") as fp, StringIO() as output_string:
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in PDFPage.get_pages(
            fp,
            page_numbers,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=check_extractable,
        ):
            interpreter.process_page(page)

        return output_string.getvalue()


def _download_document_pdf(document: Document) -> str:
    """
    Downloads the pdf locally and return the path it.

    We have to download the file to the disk because it's the easiest way to
    send the pdf to ImageMagick.

    Returns
    -------
    The path to the downloaded pdf
    """
    if not os.path.isdir(BASE_PATH):
        os.makedirs(BASE_PATH)

    filename = f"{document.edims_id}.pdf"
    tmp_filepath = os.path.join(BASE_PATH, f"{filename}.tmp")
    final_filepath = os.path.join(BASE_PATH, filename)
    logger.info("Downloading %s: %s", document.date, document.url)
    if not os.path.isfile(final_filepath):
        # WISHLIST stop using deprecated `urlretrieve`, add user-agent
        local_filename, headers = urlretrieve(document.url, tmp_filepath)
        logger.info("Downloaded to %s", local_filename)
        os.rename(local_filename, final_filepath)
    return final_filepath


def _get_pdf_page_count(filepath: str | Path) -> int:
    with open(filepath, "rb") as fp:
        return len(list(PDFPage.get_pages(fp, set(), check_extractable=False)))


def _grab_pdf_thumbnail(filepath: str | Path) -> bytes:
    """
    Returns jpeg image thumbnail of the input pdf.
    """
    logger.info("Converting pdf: %s", filepath)
    return convert(
        f"{filepath}[0]",  # force to only get 1st page
        "-thumbnail",
        "400x400",  # output size
        "-flatten",
        "jpg:-",  # output jpeg to stdout
    ).stdout


def process_pdf(document: Document) -> None:
    if not document.edims_id:
        document.scrape_status = "unscrapable"
        document.save()
        return

    filepath = _download_document_pdf(document)
    try:
        document.text = extract_text(filepath, check_extractable=False).strip()
        document.scrape_status = "scraped"
        document.page_count = _get_pdf_page_count(filepath)
    except (
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

    thumbnail = _grab_pdf_thumbnail(filepath)
    document.thumbnail.save(
        f"{document.edims_id}.jpg", ContentFile(thumbnail), save=False
    )
    document.save()
