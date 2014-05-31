import datetime

import dataset
import requests
from dateutil.parser import parse
from lxml.html import document_fromstring

# CONFIGURATION

TABLE = 'bandc_items'
PAGES = (
    # bandc_slug, id
    # bandc_slug: http://www.austintexas.gov/<bandc_slug>
    # id: http://www.austintexas.gov/cityclerk/boards_commissions/meetings/<year>_<id>_<page>.htm
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


def process_page(html):
    """
    Transform the raw html into semi-structured data.

    Pretend it's something you'd expect in a csv.

    TODO:
    * get the project name out of `text`
    * deal with video rows
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
            text = u''.join(row.xpath('./text()')).strip()
            data.append({
                'date': date,
                'type': row_type,
                'url': url,
                'text': text,
                'scraped_at': now,
            })
    return data


def save_page(data, table, bandc_slug):
    """
    Save page data to a `dataset` db table.

    TODO
    * delete previous bandc_slug/date rows because pages can change over time
    * only delete if something changed
    """
    print 'save_page', table, bandc_slug
    for row in data:
        row['banc'] = bandc_slug
        table.insert(row)


def save_pages(table=None):
    """
    Save multiple pages.
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
        n_pages = get_number_of_pages(response.text)
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


if __name__ == '__main__':
    db = dataset.connect()  # uses DATABASE_URL
    table = db[TABLE]
    save_pages(table=table)
