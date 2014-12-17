#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Usage: scrape.py [--deep] [-v|-vv]

Options:
  --deep  Crawl paginated pages to get the whole year
  -v      INFO level verbosity
  -vv     DEBUG level verbosity
"""
from __future__ import unicode_literals

import datetime
import os

from dateutil.parser import parse
from docopt import docopt
from lxml.html import document_fromstring
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
import grequests
import logging
import logging.config
import requests

from settings import PAGES, LOGGING
from models import Base, Item


logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

session = None


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


def save_page(data, bandc_slug):
    """
    Save page data to a `dataset` db table.
        """
    logger.info('save_page {}'.format(bandc_slug))

    # flag old data as dirty
    dates = set([x['date'] for x in data])
    for date in dates:
        (session.query(Item).filter_by(bandc=bandc_slug, date=date)
            .update({'dirty': True}))

    for row in data:
        # no upsert in sqlalchemy
        old = session.query(Item).filter_by(url=row['url']).first()
        if not old:
            session.add(Item(bandc=bandc_slug, dirty=False, **row))
        else:
            # ugh there has to be a better way
            old.dirty = False
            old.bandc = bandc_slug
            for k, v in row.items():
                setattr(old, k, v)

    # delete old dirty data
    session.query(Item).filter_by(dirty=True).delete()
    session.commit()


def save_pages(deep=True):
    """
    Save multiple pages.

    TODO change `deep` default to False after schema is stable.
    """
    headers = {
        'User-Agent': 'atx_bandc/0.2.0 http://atx-bandc-feed.herokuapp.com/',
    }
    # batch grab all the first pages
    urls = []
    for bandc_slug, pk, bandc_name in PAGES:
        # process first page
        urls.append(
            'http://www.austintexas.gov/cityclerk/boards_commissions/'
            'meetings/{}_{}_{}.htm'
            .format(2014, pk, '1')
        )
    rs = (grequests.get(u, headers=headers) for u in urls)
    logging.debug('queueing {} urls'.format(len(urls)))
    # size timing (includes processing, which takes awhile):
    #   1: 194s
    #   2: 150s
    #   3: 127s
    #   4: 131s
    #   5: 117s
    #   6: 113s
    responses = grequests.map(rs, size=6)

    for (bandc_slug, pk, bandc_name), response in zip(PAGES, responses):
        # process first page
        logging.info(response.url)
        if not response.ok:
            if response.status_code >= 500:
                logger.error('http {}'.format(response.status_code))
            else:
                logger.warn('no data for this year, (http {})'.format(response.status_code))
            continue
        n_pages = get_number_of_pages(response.text) if deep else 1
        data = process_page(response.text)
        if session:
            save_page(data, bandc_slug=bandc_slug)
        # process additional pages
        # TODO DRY
        for page_no in range(2, n_pages + 1):
            url = (
                'http://www.austintexas.gov/cityclerk/boards_commissions/'
                'meetings/{}_{}_{}.htm'
                .format(2014, pk, page_no)
            )
            logging.info(url)
            response = requests.get(url, headers=headers)
            assert response.status_code == 200
            data = process_page(response.text)
            if session:
                save_page(data, bandc_slug=bandc_slug)
        # TODO pause to avoid hammering


def get_number_of_pages(html):
    doc = document_fromstring(html)
    last_page_link = doc.xpath('(//a[@class="bcic_nav"])[last()]/text()')
    if not last_page_link:
        return 1
    return int(last_page_link[0].strip())


if __name__ == '__main__':
    options = docopt(__doc__)
    # print options; sys.exit()

    loglevel = ['WARNING', 'INFO', 'DEBUG'][options['-v']]
    logging.getLogger().setLevel(loglevel)

    engine = create_engine(os.environ.get('DATABASE_URL'))
    connection = engine.connect()
    Base.metadata.create_all(connection)  # checkfirst=True
    Session = sessionmaker(bind=engine)
    session = Session()
    save_pages(deep=options['--deep'])
