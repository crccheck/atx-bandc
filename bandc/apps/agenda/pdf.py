from __future__ import unicode_literals

import os
from StringIO import StringIO
from urllib import urlretrieve

import boto
import boto.s3.connection
import sh
from boto.s3.connection import S3Connection
from project_runpy import env
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

    We have to download the file to the disk because it's the easiest way to
    send the pdf to ImageMagick.

    TODO force re-download pdf because sometimes they're corrupted
    """
    if not os.path.isdir(BASE_PATH):
        os.makedirs(BASE_PATH)

    filename = document.edims_id + '.pdf'
    filepath = os.path.join(BASE_PATH, filename)
    print '{0.date}: {0.url}'.format(document)
    # Check if file was already downloaded
    if not os.path.isfile(filepath):
        # download pdf to temporary file
        print urlretrieve(document.url, filepath)  # TODO log
    return filepath


def grab_pdf_thumbnail(filepath):
    """
    Returns jpeg image thumbnail of the input pdf.
    """
    print 'converting pdf: {}'.format(filepath)
    out = sh.convert(
        filepath + '[0]',  # force to only get 1st page
        '-thumbnail', '400x400',  # output size
        '-alpha', 'remove',  # fix black border that appears
        'jpg:-',  # force to output jpeg to stdout
    )
    return out.stdout


def upload_thumb(document, thumbnail):
    """
    Upload the thumbnail for the document.

    Returns the path (key name).
    """
    s3_key = '/thumbs/{}.jpg'.format(document.edims_id)
    conn = S3Connection(
        aws_access_key_id=env.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=env.get('AWS_SECRET_ACCESS_KEY'),
        host=env.get('AWS_S3_HOST'),
        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
    )
    bucket = conn.get_bucket(env.get('AWS_BUCKET'))
    k = bucket.new_key(s3_key)
    k.set_contents_from_string(
        thumbnail,
        headers={
            'Content-Type': 'image/jpeg',
            'Cache-Control': 'public,max-age=15552000',  # 180 days
        },
    )
    k.set_canned_acl('public-read')
    return s3_key


def process_pdf(document):
    if not document.edims_id:
        document.scrape_status = 'unscrapable'
        document.save()
        return

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

    thumbnail = grab_pdf_thumbnail(filepath)
    bucket_path = upload_thumb(document, thumbnail)
    document.thumbnail = 'http://atx-bandc-pdf.crccheck.com{}'.format(bucket_path)

    document.save()
