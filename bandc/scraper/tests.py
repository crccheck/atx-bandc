import datetime
import unittest
import os

import dataset

from main import process_page, save_page, get_number_of_pages


BASE_DIR = os.path.dirname(__file__)


class PageScraper(unittest.TestCase):
    def test_process_page_works(self):
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        data = process_page(html)
        self.assertEqual(len(data), 9)
        self.assertEqual(data[0]['date'], datetime.date(2014, 6, 2))

    def test_save_page_works(self):
        # bootstrap db
        db = dataset.connect('sqlite:///:memory:')
        table = db['test']

        # bootstrap some data
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        data = process_page(html)

        save_page(data, table, 'test')
        self.assertIn('date', table.columns)
        self.assertEqual(len(table.columns), 7)
        self.assertEqual(len(table), 9)

    def test_get_number_of_pages_works(self):
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        self.assertEqual(get_number_of_pages(html), 1)
        html = open(os.path.join(BASE_DIR, 'samples/parks.html')).read()
        self.assertEqual(get_number_of_pages(html), 2)

if __name__ == '__main__':
    unittest.main()
