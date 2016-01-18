from __future__ import unicode_literals

import logging
import requests
from dateutil.parser import parse
from lxml.html import document_fromstring

from .models import Year, BandC, Meeting, Document


logger = logging.getLogger(__name__)


def populate_bandc_list():
    """
    Populate the BandC table.
    """
    response = requests.get(
        'http://www.austintexas.gov/department/boards-and-commissions')
    assert response.ok
    doc = document_fromstring(response.text)
    for option in doc.xpath('//form[@id="bc_form"]'
                            '//select[@name="board"]/option'):

        name = option.text
        path = option.values()[0]
        url = 'http://www.austintexas.gov' + path
        slug = path.split('/')[-1]

        print BandC.objects.get_or_create(
            name=name.strip(),
            slug=slug,
            homepage=url,
        )


def get_active_bandcs_for_year(year):
    """
    Check which bandcs met that year.

    Parameters
    ----------
    year: int
        The calendar year to scrape.
    """

# CONSTANTS

YEAR = 2015
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
            title = clean_text(''.join(row.xpath('./text()')).strip())
            data.append({
                'date': date,
                'type': row_type,
                'url': url,
                'title': title,
            })
    return data


def save_page(data, bandc):
    """
    Save one page worth of data.
    """
    logger.info('save_page %s', bandc)

    # # Flag old data as dirty
    # dates = set([x['date'] for x in data])
    # bandc.meetings.filter(date__in=dates).update(dirty=True)

    new_meetings = False
    for row in data:
        meeting, created = Meeting.objects.get_or_create(
            bandc=bandc, date=row['date'])
        new_meetings = new_meetings and created
        Document.objects.get_or_create(
            url=row['url'],
            defaults=dict(
                title=row['title'],
                type=row['type'],
            )
        )

    # # Delete old dirty data
    # session.query(Item).filter_by(dirty=True).delete()
    return False and new_meetings  # TODO


def get_number_of_pages(html):
    doc = document_fromstring(html)
    last_page_link = doc.xpath('(//a[@class="bcic_nav"])[last()]/text()')
    if not last_page_link:
        return 1
    return int(last_page_link[0].strip())


def pull_bandc(bandc):
    headers = {
        # TODO pull version from VERSION
        'User-Agent': 'atx_bandc/0.2.0 http://atx-bandc-feed.herokuapp.com/',
    }

    page_number = 1
    process_next = True
    while process_next:
        response = requests.get(bandc.current_meeting_url_format(page_number),
                                headers=headers)
        assert response.ok

        n_pages = get_number_of_pages(response.text)  # TODO only do this once
        data = process_page(response.text)
        page_number += 1
        process_next = save_page(data, bandc=bandc) and page_number <= n_pages
