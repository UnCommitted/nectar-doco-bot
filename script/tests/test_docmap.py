from sys import path
path.append('..')

import unittest
from unittest.mock import Mock
from unittest.mock import create_autospec

from docmap.freshdesk import FreshDeskDocumentMap

class TestDocMap(unittest.TestCase):
    def setUp(self):
        self.fd = create_autospec(FreshDeskDocumentMap)
        self.fd.load_articles = Mock()
        self.fd.load_folders = Mock()
        self.fd.load_categories = Mock()
        self.fd.load_counters = Mock()

    def test_load(self):
        self.assertIsInstance(self.fd, FreshDeskDocumentMap)

    def test_create(self):
        fd = self.fd('mapping_dir', 'article_dir', 'api_url', 'api_token')
        self.fd.assert_called_with('mapping_dir', 'article_dir', 'api_url', 'api_token')

    def test_documentmap_error(self):
        from docmap import DocumentMapError
        with self.assertRaises(DocumentMapError):
            raise DocumentMapError

if __name__ == '__main__':
    unittest.main()