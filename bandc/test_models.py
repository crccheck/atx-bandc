from __future__ import unicode_literals

import unittest

from models import Item


class ItemTest(unittest.TestCase):
    def test_edims_id_works(self):
        item = Item(
            title='test item',
            url='http://www.austintexas.gov/edims/document.cfm?id=1337',
        )
        self.assertEqual(item.edims_id, '1337')

    def test_edims_id_handles_non_edims_document(self):
        item = Item(
            title='test item',
            url='http://example.com',
        )
        self.assertEqual(item.edims_id, None)


if __name__ == '__main__':
    unittest.main()
