from django.test import TestCase

from .. import scrape_logger
from ..models import ScrapeLog


class ScrapeLoggerTests(TestCase):
    def test_init_records(self):
        with scrape_logger.init() as context:
            self.assertTrue(hasattr(context, "bandcs"))
            self.assertTrue(hasattr(context, "documents"))
            self.assertTrue(hasattr(context, "meetings"))
            self.assertTrue(hasattr(context, "errors"))

        self.assertFalse(hasattr(context, "bandcs"))
        self.assertFalse(hasattr(context, "documents"))
        self.assertFalse(hasattr(context, "meetings"))
        self.assertFalse(hasattr(context, "errors"))

    def test_record_scrape_creates_record(self):
        self.assertFalse(ScrapeLog.objects.exists())
        with scrape_logger.record_scrape():
            pass

        log = ScrapeLog.objects.get()

        self.assertTrue(str(log))
