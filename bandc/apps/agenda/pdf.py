import logging
import os
from io import StringIO
from pathlib import Path
from urllib.request import urlretrieve

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
        local_filename, _headers = urlretrieve(document.url, tmp_filepath)
        logger.info("Downloaded to %s", local_filename)
        os.rename(local_filename, final_filepath)
    return final_filepath


def _get_pdf_page_count(filepath: str | Path) -> int:
    with open(filepath, "rb") as fp:
        return len(list(PDFPage.get_pages(fp, set(), check_extractable=False)))


def _grab_pdf_thumbnail(filepath: str | Path, max_pages: int = 3) -> bytes:
    """
    Generate animated WebP thumbnail showing first N pages of PDF.

    For single-page documents, creates a static WebP.
    For multi-page documents, creates an animated WebP showing up to 3 pages.

    Args:
        filepath: Path to PDF file
        max_pages: Maximum number of pages to include in animation (default 3)

    Returns:
        WebP image as bytes (animated if multi-page, static if single-page)
    """
    from io import BytesIO

    from PIL import Image

    logger.info("Converting pdf to WebP thumbnail: %s", filepath)

    # Get total page count to avoid reading past end
    page_count = _get_pdf_page_count(filepath)
    pages_to_render = min(max_pages, page_count)

    frames = []
    for page_num in range(pages_to_render):
        # Convert each page to PNG using ImageMagick
        png_data = convert(
            f"{filepath}[{page_num}]",  # Specific page
            "-thumbnail",
            "400x400",  # Keep existing dimensions
            "-flatten",
            "png:-",
            _return_cmd=True,
        ).stdout

        # Load as PIL Image
        img = Image.open(BytesIO(png_data))
        frames.append(img)

    # Save as WebP (animated if multiple frames, static if single frame)
    output = BytesIO()
    if len(frames) == 1:
        # Single page: save as static WebP
        frames[0].save(
            output,
            format="WEBP",
            quality=80,  # Higher quality for static images
            method=4,
        )
    else:
        # Multiple pages: save as animated WebP
        frames[0].save(
            output,
            format="WEBP",
            save_all=True,  # Enable animation
            append_images=frames[1:],  # Additional frames
            duration=1000,  # 1 second per frame
            loop=0,  # Loop forever
            quality=75,  # Good quality for text documents
            method=4,  # Better compression
        )

    return output.getvalue()


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

    # Generate descriptive filename based on page count
    page_count = document.page_count or _get_pdf_page_count(filepath)
    if page_count == 1:
        filename = f"{document.edims_id}.p1.webp"
    else:
        # Limit to first 3 pages for animation
        pages_rendered = min(3, page_count)
        filename = f"{document.edims_id}.p1-p{pages_rendered}.webp"

    document.thumbnail.save(filename, ContentFile(thumbnail), save=False)
    document.save()
