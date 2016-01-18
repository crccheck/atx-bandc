from __future__ import unicode_literals

import os
from StringIO import StringIO
from urllib import urlretrieve

from pdfminer.converter import TextConverter
from pdfminer.pdfdocument import PDFDocument, PDFEncryptionError
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfparser import PDFParser
from pdfminer.psparser import PSException


BASE_PATH = '/tmp/bandc_pdfs/'  # TODO settings


def pdf_to_text(f):
    """Get the text from pdf file handle."""
    parser = PDFParser(f)
    document = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    outfp = StringIO()
    device = TextConverter(
        rsrcmgr, outfp, codec='utf-8', laparams=None,
        imagewriter=None)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(f, [], document):
        interpreter.process_page(page)
    device.close()
    f.close()
    return outfp.getvalue()


def pdf_file_path(document):
    """
    Downloads the pdf locally and return the path it.

    TODO force re-download pdf because sometimes they're corrupted
    """
    filename = document.url.rsplit('=', 2)[1] + '.pdf'
    filepath = os.path.join(BASE_PATH, filename)
    print '{0.date}: {0.url}'.format(document)
    if not os.path.isdir(BASE_PATH):
        os.makedirs(BASE_PATH)
    # check if file was already downloaded
    if not os.path.isfile(filepath):
        # download pdf to temporary file
        print urlretrieve(document.url, filepath)  # TODO log
    return filepath


def process_pdf(document):
    filepath = pdf_file_path(document)
    # Parse and save pdf text
    with open(filepath) as f:
        try:
            document.text = pdf_to_text(f).strip()
            document.scrape_status = 'scraped'
        except (PDFTextExtractionNotAllowed, PDFEncryptionError, PSException,
                # File "/usr/local/lib/python2.7/dist-packages/pdfminer/pdfpage.py", line 52, in __init__
                #     self.resources = resolve1(self.attrs['Resources'])
                # KeyError: 'Resources'
                KeyError):
            document.text = ''
            document.pdf_scraped = 'error'
        finally:
            document.save()
