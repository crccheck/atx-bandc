import datetime
import unittest

from main import process_page


class PageScraper(unittest.TestCase):
    def test_it_works(self):
        html = open('samples/music.html').read()
        data = process_page(html)
        self.assertEqual(len(data), 9)
        self.assertEqual(data[0]['date'], datetime.date(2014, 6, 2))


if __name__ == '__main__':
    unittest.main()
