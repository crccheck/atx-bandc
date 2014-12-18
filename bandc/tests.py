import datetime
import os
import unittest

from pdf import pdf_to_text
from scrape import (parse_date, clean_text, process_page,
    get_number_of_pages,
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
