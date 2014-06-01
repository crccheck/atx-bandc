import datetime
import os
import time
import unittest

import dataset

from scrape import (parse_date, clean_text, process_page, save_page,
    get_number_of_pages,
    setup_table,
    MeetingCancelled)


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
        # bootstrap db
        db = dataset.connect('sqlite:///:memory:')
        table = db['test']
        setup_table(table)

        # bootstrap some data
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        data = process_page(html)

        save_page(data, table, 'test')
        self.assertIn('date', table.columns)
        self.assertEqual(len(table.columns), 9)
        self.assertEqual(len(table), 9)
        row = table.find_one()
        scraped_at = row['scraped_at']
        url = row['url']

        time.sleep(1)  # guarantee > 1 second difference, too tired to mock
        save_page(data, table, 'test')
        # assert re-saving does not create any new rows
        self.assertEqual(len(table), 9)
        new_row = table.find_one(url=url)
        # assert row was updated, not replaced
        self.assertEqual(scraped_at, new_row['scraped_at'])

    def test_get_number_of_pages_works(self):
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        self.assertEqual(get_number_of_pages(html), 1)
        html = open(os.path.join(BASE_DIR, 'samples/parks.html')).read()
        self.assertEqual(get_number_of_pages(html), 2)


if __name__ == '__main__':
    unittest.main()
