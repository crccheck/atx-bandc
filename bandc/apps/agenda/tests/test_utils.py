import datetime
import os.path

from django.test import SimpleTestCase

from ..utils import (
    MeetingCancelled,
    parse_date, clean_text, process_page,
    get_number_of_pages,
)


BASE_DIR = os.path.dirname(__file__)


class UtilsTests(SimpleTestCase):
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
        meeting_date, doc_data = process_page(html)
        self.assertEqual(len(doc_data), 9)
        self.assertEqual(doc_data[0]['date'], datetime.date(2014, 6, 2))

    def test_get_number_of_pages_works(self):
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        self.assertEqual(get_number_of_pages(html), 1)
        html = open(os.path.join(BASE_DIR, 'samples/parks.html')).read()
        self.assertEqual(get_number_of_pages(html), 2)