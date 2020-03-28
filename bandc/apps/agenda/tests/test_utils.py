import datetime
import os.path
from unittest import mock

from django.test import TestCase

from ..factories import BandCFactory
from ..utils import (
    MeetingCancelled,
    parse_date,
    clean_text,
    process_page,
    get_number_of_pages,
    _save_page,
)


BASE_DIR = os.path.dirname(__file__)


class UtilsTests(TestCase):
    def test_parse_date_works(self):
        date = parse_date("January 13, 2014")
        self.assertEqual(date, datetime.date(2014, 1, 13))
        with self.assertRaises(MeetingCancelled):
            date = parse_date("January 28, 2014 (Cancelled)")

    def test_clean_test(self):
        fixture = (
            ("", ""),
            ("test", "test"),
            ("- May 27, 2014 PARB Agenda", "May 27, 2014 PARB Agenda"),
        )
        for input, expected in fixture:
            self.assertEqual(clean_text(input), expected)

    def test_process_page_works(self):
        html = open(os.path.join(BASE_DIR, "samples/music.html")).read()
        meeting_data, doc_data = process_page(html)
        self.assertEqual(len(doc_data), 9)
        self.assertEqual(doc_data[0]["date"], datetime.date(2014, 6, 2))

    def test_get_number_of_pages_works(self):
        html = open(os.path.join(BASE_DIR, "samples/music.html")).read()
        self.assertEqual(get_number_of_pages(html), 1)
        html = open(os.path.join(BASE_DIR, "samples/parks.html")).read()
        self.assertEqual(get_number_of_pages(html), 2)

    @mock.patch("bandc.apps.agenda.models.Document.refresh")
    def test_save_page_works(self, mock_task):
        html = open(os.path.join(BASE_DIR, "samples/music.html")).read()
        meeting_data, doc_data = process_page(html)
        bandc = BandCFactory()
        # Sanity check
        self.assertEqual(bandc.latest_meeting, None)

        created, process_next = _save_page(meeting_data, doc_data, bandc)

        self.assertEqual(len(created.meetings), 4)
        self.assertEqual(len(created.documents), 9)
        self.assertFalse(process_next)
        self.assertEqual(bandc.latest_meeting.date.isoformat(), "2014-02-03")
        self.assertEqual(bandc.latest_meeting.documents.all()[0].edims_id, 204789)
        self.assertTrue(mock_task.called)

    def test_save_page_handles_no_data(self):
        meeting_data, doc_data = [], []
        bandc = BandCFactory()
        # Sanity check
        self.assertEqual(bandc.latest_meeting, None)

        created, process_next = _save_page(meeting_data, doc_data, bandc)

        self.assertEqual(created.meetings, [])
        self.assertEqual(created.documents, [])
        self.assertFalse(process_next)
        self.assertEqual(bandc.latest_meeting, None)
