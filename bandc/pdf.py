"""
PDF Scraping.

Usage:
    pdf.py [--count=<count>] [--thumb] [--thumb-start=<pdf_id>]
    pdf.py [--single=<edims_id>]
    pdf.py [--scan]

    --count=<count>         Max number of PDFs to grab [default: 8].
    --thumb                 Create thumbnails
    --thumb-start=<pdf_id>  Start thumbnails process at this id
"""
from glob import glob
from StringIO import StringIO
from urllib import urlretrieve
import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from docopt import docopt
from pdfminer.converter import TextConverter
from pdfminer.pdfdocument import PDFDocument, PDFEncryptionError
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfparser import PDFParser
from pdfminer.psparser import PSException
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
import boto
import boto.s3.connection
import sh

from models import Base, Item


BASE_PATH = '/tmp/bandc_pdfs/'


session = None


def get_row_by_edims_id(edims_id):
    key = 'http://www.austintexas.gov/edims/document.cfm?id={}'.format(edims_id)
    return session.query(Item).filter_by(url=key).first()


def edims_has_thumb(edims_id):
    """
    This pdf has been scraped and and the thumbnail url should be set.

    Not efficient at all, but meh.
    """
    thumb_url = 'http://atx-bandc-pdf.crccheck.com/thumbs/{}.jpg'.format(edims_id)
    row = get_row_by_edims_id(edims_id)
    if row and row.thumbnail != thumb_url:
        print('updating thumbnail url for {}'.format(edims_id))
        row.thumbnail = thumb_url


def pdf_to_text(f):
    """Get the text from pdf file handle."""
    parser = PDFParser(f)
    document = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    outfp = StringIO()
    device = TextConverter(rsrcmgr, outfp, codec='utf-8', laparams=None,
       imagewriter=None)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(f, [], document):
        interpreter.process_page(page)
    device.close()
    f.close()
    return outfp.getvalue()


def grab_pdf(chunk=8):
    """
    Fill in missing pdf information.

    This is separate from the main scraper because this is more intensive and
    secondary.
    """
    result = (
        session.query(Item).filter(
            Item.pdf_scraped == None,  # NOQA
            Item.url.like('http://www.austintexas.gov/edims/document.cfm%%'),
        )
        .order_by(Item.date)
        .limit(chunk))

    for item in result:
        filename = item.url.rsplit('=', 2)[1] + '.pdf'
        filepath = os.path.join(BASE_PATH, filename)
        print u'{0.date}: {0.id}: {0.url}'.format(item)
        if not os.path.isdir(BASE_PATH):
            os.makedirs(BASE_PATH)
        # check if file was already downloaded
        if not os.path.isfile(filepath):
            # download pdf to temporary file
            print urlretrieve(item.url, filepath)  # TODO log
        # parse and save pdf text
        with open(filepath) as f:
            try:
                item.text = pdf_to_text(f).strip()
                item.pdf_scraped = True
            except (PDFTextExtractionNotAllowed, PDFEncryptionError, PSException):
                item.text = ''
                # this happens to be initialzed to NULL, so use 'False' to
                # indicate error
                item.pdf_scraped = False
    session.commit()


def grab_pdf_single(edims_id, text=True):
    """
    Download a pdf, parse the text, and upload the thumbnail all in one.

    Steps can be skipped by passing in the args as `False`
    """
    row = session.query(Item).filter(
        Item.url.like('%%{}'.format(edims_id)).first()
    )
    # download pdf to temporary file
    filename = row.url.rsplit('=', 2)[1] + '.pdf'
    filepath = os.path.join(BASE_PATH, filename)
    print(urlretrieve(row.url, filepath))  # TODO log
    if text:  # should parse pdf text
        with open(filepath) as f:
            text = pdf_to_text(f).strip()
            row.text = text
            row.pdf_scraped = True
    # turn pdf into single
    s3_key = '/thumbs/{}.jpg'.format(edims_id)
    conn = S3Connection(
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        host='objects.dreamhost.com',
        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
    )
    bucket = conn.get_bucket(os.environ.get('AWS_BUCKET'))
    out = sh.convert(
        filepath + '[0]',  # force to only get 1st page
        '-thumbnail', '400x400',  # output size
        '-alpha', 'remove',  # fix black border that appears
        'jpg:-',  # force to output jpeg to stdout
    )
    k = Key(bucket)
    k.key = s3_key
    k.set_metadata('Content-Type', 'image/jpeg')
    k.set_contents_from_string(out.stdout)
    k.set_canned_acl('public-read')
    row.thumbnail = 'http://atx-bandc-pdf.crccheck.com/thumbs/{}.jpg'.format(edims_id)
    session.commit()


def turn_pdfs_into_images():
    """
    Run through the tmp directory and turn pdfs into thumbnails.

    TODO save thumb url back to db. Right now need to re-run with scan.
    """
    conn = S3Connection(
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        host='objects.dreamhost.com',
        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
    )
    bucket = conn.get_bucket(os.environ.get('AWS_BUCKET'))
    started = not options['--thumb-start']
    for filepath in glob(os.path.join(BASE_PATH, '*.pdf')):
        filepath.rsplit('.', 2)[0]
        filename = os.path.basename(filepath)
        edims_id = os.path.splitext(filename)[0]
        if not started:
            if edims_id == options['--thumb-start']:
                started = True
            else:
                continue
        s3_key = '/thumbs/{}.jpg'.format(edims_id)
        print filepath, edims_id, s3_key
        k = bucket.get_key(s3_key)
        if k:
            print '.already exists'
            edims_has_thumb(edims_id)
            continue
        out = sh.convert(
            filepath + '[0]',  # force to only get 1st page
            '-thumbnail', '400x400',  # output size
            '-alpha', 'remove',  # fix black border that appears
            'jpg:-',  # force to output jpeg to stdout
        )
        k = Key(bucket)
        k.key = s3_key
        k.set_metadata('Content-Type', 'image/jpeg')
        k.set_contents_from_string(out.stdout)
        k.set_canned_acl('public-read')
        edims_has_thumb(edims_id)
    session.commit()


def scan_for_missing_thumbnails():
    """Look for parsed pdfs that don't have thumbnails and give it to them."""
    results = session.query(Item).filter_by(thumbnail=None, pdf_scraped=True)
    for row in results:
        edims_id = row.url.rsplit('=', 2)[-1]
        grab_pdf_single(edims_id, text=False)  # don't need to reparse text


if __name__ == '__main__':
    options = docopt(__doc__)
    # print(options)

    engine = create_engine(os.environ.get('DATABASE_URL'))
    connection = engine.connect()
    Base.metadata.create_all(connection)  # checkfirst=True
    Session = sessionmaker(bind=engine)
    session = Session()

    if options['--single']:
        grab_pdf_single(options['--single'])
    elif options['--scan']:
        scan_for_missing_thumbnails()
    else:
        count = int(options['--count'])
        grab_pdf(count)
        if options['--thumb']:
            turn_pdfs_into_images()
