import os
import unittest

from ..pdf import pdf_to_text


BASE_DIR = os.path.dirname(__file__)


class PdfTest(unittest.TestCase):
    def test_process_pdf_works(self):
        f = open(os.path.join(
            BASE_DIR,
            'samples/document_53B86715-0261-C36F-8C2F847EF15AD639.pdf'), 'rb')
        out = pdf_to_text(f)
        self.assertTrue(out)
