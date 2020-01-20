import os
import unittest

from ..pdf import pdf_page_count


BASE_DIR = os.path.dirname(__file__)


class PdfTest(unittest.TestCase):
    def test_pdf_page_count(self):
        filepath = os.path.join(
            BASE_DIR, "samples/document_53B86715-0261-C36F-8C2F847EF15AD639.pdf"
        )
        self.assertEqual(pdf_page_count(filepath), 5)
