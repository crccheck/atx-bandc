from __future__ import unicode_literals

import datetime
import sys

from dateutil.parser import parse
from lxml.html import document_fromstring
import dataset
import grequests
import requests
import sqlalchemy.types

from settings import TABLE, PAGES

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
                # 'text': '',  # don't overwrite
                # 'pdf_scraped': ''.  # don't overwrite
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
    # batch grab all the first pages
    urls = []
    for bandc_slug, pk, bandc_name in PAGES:
        # process first page
        urls.append(
            'http://www.austintexas.gov/cityclerk/boards_commissions/'
            'meetings/{}_{}_{}.htm'
            .format(2014, pk, '1')
        )
    rs = (grequests.get(u) for u in urls)
    print 'queueing {} urls'.format(len(urls))
    # 5: 117s
    responses = grequests.map(rs, size=1)

    for (bandc_slug, pk, bandc_name), response in zip(PAGES, responses):
        # process first page
        print response.url
        if not response.ok:
            print 'WARNING: no data for this year, (http {})'.format(response.status_code)
            continue
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
    """Sets up the table schema if not already setup."""
    if 'date' not in table.columns:
        table.create_column('date', sqlalchemy.types.Date)
    if 'dirty' not in table.columns:
        table.create_column('dirty', sqlalchemy.types.Boolean)
    if 'pdf_scraped' not in table.columns:
        table.create_column('pdf_scraped', sqlalchemy.types.Boolean)
    if 'thumbnail' not in table.columns:
        table.create_column('thumbnail', sqlalchemy.types.String)
    if 'text' not in table.columns:
        table.create_column('text', sqlalchemy.types.Text)
    if 'url' not in table.columns:
        table.create_column('url', sqlalchemy.types.String)
        table.create_index(['url'])  # XXX broken


if __name__ == '__main__':
    db = dataset.connect()  # uses DATABASE_URL
    table = db[TABLE]
    setup_table(table)
    deep = '--deep' in sys.argv[1:]
    save_pages(table=table, deep=deep)
