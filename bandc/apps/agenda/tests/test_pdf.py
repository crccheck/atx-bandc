import pathlib
from unittest.mock import patch

from django.test import TestCase

from ..factories import DocumentFactory
from ..pdf import _get_pdf_page_count, _grab_pdf_thumbnail, process_pdf

BASE_DIR = pathlib.Path(__file__).parent


class PdfTest(TestCase):
    def test_get_pdf_page_count(self):
        filepath = BASE_DIR / "samples/document_53B86715-0261-C36F-8C2F847EF15AD639.pdf"
        self.assertEqual(_get_pdf_page_count(filepath), 5)

    def test_get_pdf_page_count_handles_pdftextextractionnotallowed(self):
        filepath = BASE_DIR / "samples/edims_333704.pdf"
        with self.assertLogs("pdfminer.pdfpage", level="WARNING"):
            self.assertEqual(_get_pdf_page_count(filepath), 1)

    @patch("bandc.apps.agenda.pdf._download_document_pdf")
    def test_process_pdf_singlepage(self, mock_download):
        """Single-page PDFs should get static WebP with descriptive name."""
        mock_download.return_value = str(BASE_DIR / "samples/edims_333704.pdf")
        doc = DocumentFactory(
            url="http://www.austintexas.gov/edims/document.cfm?id=333704",
            edims_id=333704,
        )

        with self.assertLogs("pdfminer.pdfpage", level="WARNING"):
            process_pdf(doc)

        doc.refresh_from_db()

        # Should have WebP thumbnail with page indicator in filename
        self.assertTrue(doc.thumbnail)
        self.assertIn(".webp", doc.thumbnail.name)
        self.assertEqual(doc.scrape_status, "scraped")
        self.assertTrue(doc.text.startswith("Regular \nMeeting"))

        # Filename should indicate single page (e.g., 333704.p1.webp)
        # Django may add a random suffix if file exists
        self.assertRegex(
            doc.thumbnail.name,
            r"333704(_[A-Za-z0-9]+)?\.p1\.webp$",
            "Single-page thumbnail should have format {id}.p1.webp",
        )

    @patch("bandc.apps.agenda.pdf._grab_pdf_thumbnail")
    @patch("bandc.apps.agenda.pdf._download_document_pdf")
    def test_extracts_extraction_not_allowed(self, mock_download, mock_thumbnail):
        mock_download.return_value = str(BASE_DIR / "samples/edims_333704.pdf")
        mock_thumbnail.return_value = b""
        doc = DocumentFactory(
            url="http://www.austintexas.gov/edims/document.cfm?id=333705",
            edims_id=333705,
        )

        with self.assertLogs("pdfminer.pdfpage", level="WARNING"):
            process_pdf(doc)
        doc.refresh_from_db()

        self.assertEqual(doc.scrape_status, "scraped")
        self.assertTrue(doc.text.startswith("Regular \nMeeting"))

    @patch("bandc.apps.agenda.pdf._download_document_pdf")
    def test_process_pdf_multipage(self, mock_download):
        """Multi-page PDFs should get animated WebP with descriptive name."""
        mock_download.return_value = str(
            BASE_DIR / "samples/document_53B86715-0261-C36F-8C2F847EF15AD639.pdf"
        )
        doc = DocumentFactory(
            url="http://www.austintexas.gov/edims/document.cfm?id=999999",
            edims_id=999999,
        )

        process_pdf(doc)

        doc.refresh_from_db()

        # Should have WebP thumbnail with page range in filename
        self.assertTrue(doc.thumbnail)
        self.assertIn(".webp", doc.thumbnail.name)
        self.assertEqual(doc.scrape_status, "scraped")

        # Filename should indicate page range (e.g., 999999.p1-p3.webp)
        # This PDF has 5 pages, so it should show p1-p3
        # Django may add a random suffix if file exists
        self.assertRegex(
            doc.thumbnail.name,
            r"999999(_[A-Za-z0-9]+)?\.p1-p3\.webp$",
            "Multi-page thumbnail should have format {id}.p1-p3.webp",
        )

    @patch("bandc.apps.agenda.pdf._grab_pdf_thumbnail")
    @patch("bandc.apps.agenda.pdf._download_document_pdf")
    def test_extract_text_type_error_fixed(self, mock_download, mock_thumbnail):
        """This used to error, but a pdfminer upgrade fixed this."""
        mock_download.return_value = str(BASE_DIR / "samples/edims_334453.pdf")
        mock_thumbnail.return_value = b""
        doc = DocumentFactory(
            url="http://www.austintexas.gov/edims/document.cfm?id=334454",
            edims_id=334454,
        )

        process_pdf(doc)

        doc.refresh_from_db()
        self.assertIn("All of the items above were recommendations by the", doc.text)
        self.assertEqual(doc.scrape_status, "scraped")

    def test_grab_pdf_thumbnail(self):
        """Should generate valid WebP thumbnail."""
        filepath = BASE_DIR / "samples/edims_334453.pdf"

        with self.assertLogs("bandc.apps.agenda.pdf", level="INFO"):
            thumbnail = _grab_pdf_thumbnail(filepath)

        # Verify it's valid WebP (check for WEBP/VP8 signature)
        # WebP signature: RIFF....WEBP or RIFF....VP8
        self.assertTrue(
            thumbnail[:4] == b"RIFF" and b"WEBP" in thumbnail[:20],
            "Thumbnail should be WebP format",
        )

        # Verify dimensions with Pillow
        from io import BytesIO

        from PIL import Image

        img = Image.open(BytesIO(thumbnail))
        self.assertEqual(img.format, "WEBP")
        self.assertLessEqual(img.width, 400)
        self.assertLessEqual(img.height, 400)

        # For multi-page PDFs, verify animation (max 3 frames)
        if img.n_frames > 1:
            self.assertGreaterEqual(img.n_frames, 2)
            self.assertLessEqual(img.n_frames, 3)

        # File should be reasonable size for text documents
        self.assertLess(len(thumbnail), 80_000)  # Less than 80KB
