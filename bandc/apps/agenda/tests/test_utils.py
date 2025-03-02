import datetime
import os.path
from unittest import mock

from django.test import TestCase

from .. import scrape_logger
from ..factories import BandCFactory
from ..models import Document
from ..utils import (
    MeetingCancelledError,
    _save_page,
    clean_text,
    get_number_of_pages,
    parse_date,
    process_page,
)

BASE_DIR = os.path.dirname(__file__)


class UtilsTests(TestCase):
    def test_parse_date_works(self):
        date = parse_date("January 13, 2014")
        self.assertEqual(date, datetime.date(2014, 1, 13))
        with self.assertRaises(MeetingCancelledError):
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
        with open(os.path.join(BASE_DIR, "samples/music.html")) as fh:
            html = fh.read()
        meeting_data, doc_data = process_page(html)
        self.assertEqual(len(meeting_data), 7)
        self.assertEqual(len(doc_data), 28)
        self.assertEqual(doc_data[0]["date"], datetime.date(2014, 12, 1))

    def test_process_page_works_with_strong_elem(self):
        with open(os.path.join(BASE_DIR, "samples/2016_134_1.htm")) as fh:
            html = fh.read()
        meeting_data, doc_data = process_page(html)
        self.assertEqual(len(meeting_data), 5)
        self.assertEqual(len(doc_data), 16)
        self.assertEqual(doc_data[0]["date"], datetime.date(2016, 5, 19))

    def test_get_number_of_pages_works(self):
        with open(os.path.join(BASE_DIR, "samples/music.html")) as fh:
            html = fh.read()
        self.assertEqual(get_number_of_pages(html), 1)

        with open(os.path.join(BASE_DIR, "samples/parks.html")) as fh:
            html = fh.read()
        self.assertEqual(get_number_of_pages(html), 5)

    @mock.patch("bandc.apps.agenda.models.Document.refresh")
    def test_save_page_works(self, mock_task):
        with open(os.path.join(BASE_DIR, "samples/music.html")) as fh:
            html = fh.read()
        meeting_data, doc_data = process_page(html)
        bandc = BandCFactory()
        # Sanity check
        self.assertEqual(bandc.latest_meeting, None)

        with self.assertLogs("bandc.apps.agenda.utils", level="INFO"):
            process_next = _save_page(meeting_data, doc_data, bandc)

        self.assertFalse(process_next)
        self.assertEqual(bandc.latest_meeting.date.isoformat(), "2014-02-03")
        self.assertEqual(bandc.latest_meeting.documents.all()[0].edims_id, 204789)
        self.assertTrue(mock_task.called)

    def test_save_page_handles_no_data(self):
        meeting_data, doc_data = [], []
        bandc = BandCFactory()
        # Sanity check
        self.assertEqual(bandc.latest_meeting, None)

        with self.assertLogs("bandc.apps.agenda.utils", level="INFO"):
            process_next = _save_page(meeting_data, doc_data, bandc)

        self.assertFalse(process_next)
        self.assertEqual(bandc.latest_meeting, None)

    @mock.patch("bandc.apps.agenda.models.Document.refresh")
    def test_save_page_handles_duplicate_urls(self, mock_task):
        """Over time, we may see the same document posted in an old URL."""
        with open(os.path.join(BASE_DIR, "samples/parks.html")) as fh:
            html = fh.read()
        meeting_data, doc_data = process_page(html)
        bandc = BandCFactory()
        with self.assertLogs("bandc.apps.agenda.utils", level="INFO"):
            _save_page(meeting_data, doc_data, bandc)
        self.assertEqual(Document.objects.filter(active=True).count(), 100)

        for row in doc_data:
            row["url"] = row["url"].replace(
                "services.austintexas.gov", "www.austintexas.gov"
            )

        with self.assertLogs("bandc.apps.agenda.utils", level="INFO"):
            _save_page(meeting_data, doc_data, bandc)
        # Assert stale_documents did not actually change anything
        self.assertEqual(Document.objects.filter(active=True).count(), 100)

    @mock.patch("bandc.apps.agenda.models.Document.refresh")
    def test_save_page_logs_to_scrape_logger(self, mock_task):
        with open(os.path.join(BASE_DIR, "samples/music.html")) as fh:
            html = fh.read()
        meeting_data, doc_data = process_page(html)
        bandc = BandCFactory()
        # Sanity check
        self.assertEqual(bandc.latest_meeting, None)

        with scrape_logger.init() as context:
            with self.assertLogs("bandc.apps.agenda.utils", level="INFO"):
                _save_page(meeting_data, doc_data, bandc)

            self.assertEqual(len(context.meetings), 7)
            self.assertEqual(len(context.documents), 28)
