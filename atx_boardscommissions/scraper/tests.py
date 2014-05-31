import unittest
from main import process


class PageScraper(unittest.TestCase):
    def test_it_works(self):
        html = open('samples/music.html').read()
        data = process(html)
        print data


if __name__ == '__main__':
    unittest.main()
