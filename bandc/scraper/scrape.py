import datetime
import os
import sys
from urllib import urlretrieve

from StringIO import StringIO
import dataset
import requests
import sqlalchemy.types
from dateutil.parser import parse
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from lxml.html import document_fromstring

# CONFIGURATION

TABLE = 'bandc_items'
PAGES = (
    # bandc_slug, id
    # bandc_slug: http://www.austintexas.gov/<bandc_slug>
    # id: http://www.austintexas.gov/cityclerk/boards_commissions/meetings/
    #     <year>_<id>_<page>.htm
    ('parb', '39'),
    ('musiccomm', '12'),
)

# CONSTANTS

MEETING_DATE = 'bcic_mtgdate'
DOCUMENT = 'bcic_doc'


class MeetingCancelled(Exception):
    pass


def parse_date(string):
    """
    Turn a date row into a datetime.date instance.
    """
    if 'cancel' in string.lower():
        raise MeetingCancelled('Meeting Cancelled')
    return parse(string).date()


def clean_text(text):
    return text.lstrip('- ')


def process_page(html):
    """
    Transform the raw html into semi-structured data.

    Pretend it's something you'd expect in a csv.

    TODO:
    * get the project name out of `title`
    * deal with video rows
    TODO handle when a previously published meeting gets cancelled
    """
    doc = document_fromstring(html)
    date = ''
    data = []
    now = datetime.datetime.now()
    for row in doc.xpath('//div[@id="bcic"]/h5'):
        row_class = row.attrib['class']  # assume each has only one css class
        if row_class == MEETING_DATE:
            try:
                date = parse_date(row.text)
            except MeetingCancelled:
                date = None
        elif date and row_class == DOCUMENT:
            row_type = row.xpath('./a/b/text()')[0]
            url = row.xpath('./a/@href')[0]
            title = clean_text(u''.join(row.xpath('./text()')).strip())
            data.append({
                'date': date,
                'type': row_type,
                'url': url,
                'title': title,
                'text': '',
                'scraped_at': now,
            })
    return data


def save_page(data, table, bandc_slug):
    """
    Save page data to a `dataset` db table.
        """
    print 'save_page', table, bandc_slug

    # delete old data
    dates = set([x['date'] for x in data])
    for date in dates:
        update_data = dict(
            # SET
            dirty=True,
            # WHERE
            bandc=bandc_slug,
            date=date,
        )
        table.update(update_data, ('bandc', 'date'))

    for row in data:
        row['bandc'] = bandc_slug
        row['dirty'] = False
        table.upsert(row, ['url'])

    table.delete(dirty=True)


def save_pages(table=None, deep=True):
    """
    Save multiple pages.

    TODO change `deep` default to False after schema is stable.
    """
    for bandc_slug, pk in PAGES:
        # process first page
        url = (
            'http://www.austintexas.gov/cityclerk/boards_commissions/'
            'meetings/{}_{}_{}.htm'
            .format(2014, pk, '1')
        )
        print url
        response = requests.get(url)
        assert response.status_code == 200
        n_pages = get_number_of_pages(response.text) if deep else 1
        data = process_page(response.text)
        if table is not None:
            save_page(data, table, bandc_slug=bandc_slug)
        # process additional pages
        # TODO DRY
        for page_no in range(2, n_pages + 1):
            url = (
                'http://www.austintexas.gov/cityclerk/boards_commissions/'
                'meetings/{}_{}_{}.htm'
                .format(2014, pk, page_no)
            )
            print url
            response = requests.get(url)
            assert response.status_code == 200
            data = process_page(response.text)
            if table is not None:
                save_page(data, table, bandc_slug=bandc_slug)
        # TODO pause to avoid hammering


def get_number_of_pages(html):
    doc = document_fromstring(html)
    last_page_link = doc.xpath('(//a[@class="bcic_nav"])[last()]/text()')
    if not last_page_link:
        return 1
    return int(last_page_link[0].strip())


def setup_table(table):
    if 'date' not in table.columns:
        table.create_column('date', sqlalchemy.types.Date)
    if 'dirty' not in table.columns:
        table.create_column('dirty', sqlalchemy.types.Boolean)
    if 'text' not in table.columns:
        table.create_column('text', sqlalchemy.types.Text)
    if 'url' not in table.columns:
        table.create_column('url', sqlalchemy.types.String)
        table.create_index(['url'])  # XXX broken


def pdf_to_text(f):
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

    If no text was found in the pdf, fill in something anyways just so we know
    we already tried.

    This is separate from the main scraper because this is more intensive and
    secondary.
    """
    db = dataset.connect()  # uses DATABASE_URL
    table = db.load_table(TABLE)
    result = db.query("SELECT id, url FROM {} WHERE url LIKE '{}%%' "
        "AND text='' ORDER BY date DESC LIMIT {}".format(
            TABLE,
            'http://www.austintexas.gov/edims/document.cfm',
            chunk,
        )
    )
    base_path = '/tmp/bandc_pdfs/'
    for row in result:
        filename = row['url'].rsplit('=', 2)[1] + '.pdf'
        filepath = os.path.join(base_path, filename)
        print row, filepath
        if not os.path.isdir(base_path):
            os.makedirs(base_path)
        # check if file was already downloaded
        if not os.path.isfile(filepath):
            # download pdf to temporary file
            print urlretrieve(row['url'], filepath)  # TODO log
        # parse and save pdf text
        with open(filepath) as f:
            text = pdf_to_text(f).strip()
            if not text:
                text = 'no text found in pdf'
            data = dict(
                # set
                text=text,
                # where
                id=row['id'],
            )
            table.update(data, ['id'], ensure=False)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'pdf':
        grab_pdf()
        exit()
    if len(sys.argv) > 1 and sys.argv[1] == 'scrape':
        db = dataset.connect()  # uses DATABASE_URL
        table = db[TABLE]
        setup_table(table)
        deep = '--deep' in sys.argv[2:]
        save_pages(table=table, deep=deep)
