import os
import unittest
from unittest.mock import patch

from ..pdf import _get_pdf_page_count, process_pdf
from ..factories import DocumentFactory


BASE_DIR = os.path.dirname(__file__)


class PdfTest(unittest.TestCase):
    def test_get_pdf_page_count(self):
        filepath = os.path.join(
            BASE_DIR, "samples/document_53B86715-0261-C36F-8C2F847EF15AD639.pdf"
        )
        self.assertEqual(_get_pdf_page_count(filepath), 5)

    def test_get_pdf_page_count_handles_PDFTextExtractionNotAllowed(self):
        filepath = os.path.join(BASE_DIR, "samples/edims_333704.pdf")
        self.assertEqual(_get_pdf_page_count(filepath), 1)

    @patch("bandc.apps.agenda.pdf._grab_pdf_thumbnail")
    @patch("bandc.apps.agenda.pdf._download_document_pdf")
    def test_extracts_extraction_not_allowed(self, mock_download, mock_thumbnail):
        mock_download.return_value = os.path.join(BASE_DIR, "samples/edims_333704.pdf")
        mock_thumbnail.return_value = b""
        doc = DocumentFactory(
            url="http://www.austintexas.gov/edims/document.cfm?id=333704",
            edims_id=333704,
        )

        process_pdf(doc)
        doc.refresh_from_db()

        self.assertEqual(doc.scrape_status, "scraped")
        self.assertTrue(doc.text.startswith("Regular \nMeeting"))

    @patch("bandc.apps.agenda.pdf._grab_pdf_thumbnail")
    @patch("bandc.apps.agenda.pdf._download_document_pdf")
    def test_extract_text_type_error(self, mock_download, mock_thumbnail):
        mock_download.return_value = os.path.join(BASE_DIR, "samples/edims_334453.pdf")
        mock_thumbnail.return_value = b""
        doc = DocumentFactory(
            url="http://www.austintexas.gov/edims/document.cfm?id=334453",
            edims_id=334453,
        )

        process_pdf(doc)
        doc.refresh_from_db()

        self.assertEqual(doc.scrape_status, "error")
        self.assertEqual(doc.text, "")
