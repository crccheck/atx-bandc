"""
PDF Scraping.

Usage:
    pdf.py process <edims_id> [-v|-vv]
    pdf.py scrape [-v|-vv] [options]
    pdf.py thumbnails [-v|-vv]

Options:
  --count=<count>  Max number of PDFs to grab [default: 8].
  -v               INFO level verbosity
  -vv     DEBUG level verbosity
"""
import logging
import logging.config
import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from docopt import docopt
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
import boto
import boto.s3.connection
import sh

from models import Base, Item
from settings import LOGGING


logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

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


def grab_pdf_single(edims_id, scrape_text=True):
    """
    Download a pdf, parse the text, and upload the thumbnail all in one.

    Steps can be skipped by passing in the args as `False`
    """
    # FIXME why does this not want to work?
    if edims_id == '223378':
        return
    url = 'http://www.austintexas.gov/edims/document.cfm?id={}'.format(edims_id)
    item = session.query(Item).filter(Item.url == url).first()
    filepath = pdf_file_path(item)
    if scrape_text:  # should parse pdf text
        with open(filepath) as f:
            text = pdf_to_text(f).strip()
            item.text = text
            item.pdf_scraped = True
    # turn pdf into single
    s3_key = '/thumbs/{}.jpg'.format(edims_id)
    conn = S3Connection(
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        host='objects.dreamhost.com',
        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
    )
    bucket = conn.get_bucket(os.environ.get('AWS_BUCKET'))
    print 'converting pdf: {}'.format(filepath)
    out = sh.convert(
        filepath + '[0]',  # force to only get 1st page
        '-thumbnail', '400x400',  # output size
        '-alpha', 'remove',  # fix black border that appears
        'jpg:-',  # force to output jpeg to stdout
    )
    jpeg_image = out.stdout
    k = bucket.new_key(s3_key)
    k.set_contents_from_string(
        jpeg_image,
        headers={
            'Content-Type': 'image/jpeg',
            'Cache-Control': 'public,max-age=15552000',  # 180 days
        },
    )
    k.set_canned_acl('public-read')
    item.thumbnail = 'http://atx-bandc-pdf.crccheck.com/thumbs/{}.jpg'.format(edims_id)
    session.commit()


def thumbnails():
    """Look for parsed pdfs that don't have thumbnails and give it to them."""
    queryset = session.query(Item).filter_by(thumbnail=None, pdf_scraped=True)
    for item in queryset:
        edims_id = item.edims_id
        grab_pdf_single(edims_id, scrape_text=False)  # don't need to reparse text


if __name__ == '__main__':
    options = docopt(__doc__)
    # print(options); exit()

    loglevel = ['WARNING', 'INFO', 'DEBUG'][options['-v']]
    logging.getLogger().setLevel(loglevel)

    engine = create_engine(os.environ.get('DATABASE_URL'))
    connection = engine.connect()
    Base.metadata.create_all(connection)  # checkfirst=True
    Session = sessionmaker(bind=engine)
    session = Session()

    if options['process']:
        grab_pdf_single(options['<edims_id>'])
    elif options['thumbnails']:
        thumbnails()
    elif options['scrape']:
        count = int(options['--count'])
        grab_pdf(count)
