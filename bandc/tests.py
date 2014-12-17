import datetime
import os
import time
import unittest

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

from pdf import pdf_to_text
from scrape import (parse_date, clean_text, process_page, save_page,
    get_number_of_pages,
    MeetingCancelled)
from models import Base, Item


BASE_DIR = os.path.dirname(__file__)


class PageScraper(unittest.TestCase):
    def test_parse_date_works(self):
        date = parse_date('January 13, 2014')
        self.assertEqual(date, datetime.date(2014, 1, 13))
        with self.assertRaises(MeetingCancelled):
            date = parse_date('January 28, 2014 (Cancelled)')

    def test_clean_test(self):
        fixture = (
            ('', ''),
            ('test', 'test'),
            ('- May 27, 2014 PARB Agenda', 'May 27, 2014 PARB Agenda')
        )
        for input, expected in fixture:
            self.assertEqual(clean_text(input), expected)

    def test_process_page_works(self):
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        data = process_page(html)
        self.assertEqual(len(data), 9)
        self.assertEqual(data[0]['date'], datetime.date(2014, 6, 2))

    def test_save_page_works(self):
        # setup
        engine = create_engine('sqlite:///:memory:')
        connection = engine.connect()
        Base.metadata.create_all(connection)
        Session = sessionmaker(bind=engine)
        session = Session()

        # bootstrap some data
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        data = process_page(html)

        save_page(data, session, 'test')
        n_rows = session.query(Item).count()
        self.assertEqual(n_rows, 9)
        row = session.query(Item).first()
        scraped_at = row.scraped_at
        url = row.url
        old_pk = row.id

        time.sleep(1)  # guarantee > 1 second difference, too tired to mock
        save_page(data, session, 'test')
        # assert re-saving does not create any new rows
        n_rows = session.query(Item).count()
        self.assertEqual(n_rows, 9)
        new_row = session.query(Item).filter_by(url=url).first()
        # assert row was updated, not replaced
        self.assertEqual(old_pk, new_row.id)
        self.assertEqual(scraped_at, new_row.scraped_at)

        connection.close()
        engine.dispose()

    def test_save_page_updates_text(self):
        # setup
        engine = create_engine('sqlite:///:memory:')
        connection = engine.connect()
        Base.metadata.create_all(connection)
        Session = sessionmaker(bind=engine)
        session = Session()

        # bootstrap some data
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        data = process_page(html)

        save_page(data, session, 'test')
        old_item = session.query(Item).first()
        url = old_item.url
        old_id = old_item.id
        old_item.text = 'test123'

        save_page(data, session, 'test')
        new_item = session.query(Item).filter_by(url=url).first()
        self.assertEqual(new_item.text, 'test123')
        # assert we did an update, not an insert
        self.assertEqual(new_item.id, old_id)

    def test_get_number_of_pages_works(self):
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        self.assertEqual(get_number_of_pages(html), 1)
        html = open(os.path.join(BASE_DIR, 'samples/parks.html')).read()
        self.assertEqual(get_number_of_pages(html), 2)


class PdfTest(unittest.TestCase):
    def test_process_pdf_works(self):
        f = open(os.path.join(BASE_DIR,
            'samples/document_53B86715-0261-C36F-8C2F847EF15AD639.pdf'), 'rb')
        out = pdf_to_text(f)
        self.assertTrue(out)


if __name__ == '__main__':
    unittest.main()
