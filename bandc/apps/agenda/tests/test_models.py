import unittest
from unittest.mock import Mock, PropertyMock

from ..factories import DocumentFactory


class DocumentThumbnailTest(unittest.TestCase):
    def test_thumbnail_dimensions_return_actual_values(self):
        doc = DocumentFactory()
        doc.thumbnail = Mock()
        doc.thumbnail.width = 308
        doc.thumbnail.height = 400

        self.assertEqual(doc.thumbnail_width, 308)
        self.assertEqual(doc.thumbnail_height, 400)

    def test_thumbnail_dimensions_return_none_on_file_not_found(self):
        doc = DocumentFactory()
        doc.thumbnail = Mock()
        type(doc.thumbnail).width = PropertyMock(side_effect=FileNotFoundError)
        type(doc.thumbnail).height = PropertyMock(side_effect=FileNotFoundError)

        self.assertIsNone(doc.thumbnail_width)
        self.assertIsNone(doc.thumbnail_height)

    def test_thumbnail_dimensions_return_none_when_no_thumbnail(self):
        doc = DocumentFactory(thumbnail=None)

        self.assertIsNone(doc.thumbnail_width)
        self.assertIsNone(doc.thumbnail_height)
