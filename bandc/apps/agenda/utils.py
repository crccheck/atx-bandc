from __future__ import unicode_literals

import logging
import requests
from dateutil.parser import parse
from lxml import etree
from lxml.html import document_fromstring
from obj_update import obj_update_or_create

from .models import BandC, Meeting, Document


# CONSTANTS

YEAR = 2015
MEETING_DATE = 'bcic_mtgdate'
MEETING_TITLE = 'bcic_mtgtype'
DOCUMENT = 'bcic_doc'


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


def inner_html(node):
    """
    Equivalent to doing node.innerHTML if this were JavaScript.

    # http://stackoverflow.com/questions/6123351/equivalent-to-innerhtml-when-using-lxml-html-to-parse-html/6396097#6396097
    """
    return (
        (node.text or '') +
        ''.join([etree.tostring(child) for child in node.iterchildren()])
    )


def process_page(html):
    """
    Transform the raw html into semi-structured data.

    Returns
    -------
    tuple (dict, dict)
        Returns all the meeting data, and all the documents found.
    """
    doc = document_fromstring(html)
    date = ''
    meeting_data = []
    doc_data = []
    for row in doc.xpath('//div[@id="bcic"]/h5'):
        row_class = row.attrib['class']  # assume each has only one css class
        if row_class == MEETING_DATE:
            try:
                date = parse_date(row.text)
            except MeetingCancelled:
                date = None
        elif date and row_class == MEETING_TITLE:
            # XXX assume all meeting date rows are followed by meeting title
            meeting_data.append({
                'date': date,
                'title': inner_html(row),
            })
        elif date and row_class == DOCUMENT:
            row_type = row.xpath('./a/b/text()')[0]
            url = row.xpath('./a/@href')[0]
            title = clean_text(''.join(row.xpath('./text()')).strip())
            doc_data.append({
                'date': date,
                'type': row_type,
                'url': url,
                'title': title,
            })
    return meeting_data, doc_data


def save_page(meeting_data, doc_data, bandc):
    """
    Save one page worth of data.
    """
    logger.info('save_page %s', bandc)

    new_meetings = False
    meetings = {}
    for row in meeting_data:
        meeting, created = obj_update_or_create(
            Meeting,
            bandc=bandc, date=row['date'],
            defaults={'title': row['title']})

        new_meetings = new_meetings and created
        meetings[row['date']] = {
            'meeting': meeting,
            'docs': set(meeting.documents.values_list('url', flat=True)),
        }

    for row in doc_data:
        doc, created = Document.objects.get_or_create(
            url=row['url'],
            meeting=meetings[row['date']]['meeting'],
            defaults=dict(
                title=row['title'],
                type=row['type'],
            )
        )
        if not created:
            try:
                meetings[row['date']]['docs'].remove(row['url'])
            except KeyError:
                pass

    stale_documents = []
    for meeting in meetings.values():
        stale_documents.extend(meeting['docs'])

    if stale_documents:
        print 'These docs are stale:', stale_documents
        Document.objects.filter(url__in=stale_documents).update(active=False)

    return False and new_meetings  # TODO


def get_number_of_pages(html):
    doc = document_fromstring(html)
    last_page_link = doc.xpath('(//a[@class="bcic_nav"])[last()]/text()')
    if not last_page_link:
        return 1
    return int(last_page_link[0].strip())


def pull_bandc(bandc):
    """
    Get info about all the meetings for the most recent year.
    """
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
        meeting_data, doc_data = process_page(response.text)
        page_number += 1
        process_next = save_page(meeting_data, doc_data, bandc=bandc) and (
            page_number <= n_pages)