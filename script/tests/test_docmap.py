from sys import path
path.append('..')

import unittest
from unittest.mock import patch
from unittest.mock import create_autospec

from docmap import DocumentMap
from docmap.freshdesk import FreshDeskDocumentMap

class TestDocMapDef(unittest.TestCase):
    def setUp(self):
        self.fd = create_autospec(FreshDeskDocumentMap)

    def test_load(self):
        self.assertIsInstance(self.fd, FreshDeskDocumentMap)
        self.fd.load_mappings()
        assert self.fd.load_mappings.called

    def test_create_instance(self):
        fd = self.fd('mapping_dir', 'article_dir', 'api_url', 'api_token')
        self.fd.assert_called_with('mapping_dir', 'article_dir', 'api_url', 'api_token')

    def test_documentmap_error(self):
        from docmap import DocumentMapError
        with self.assertRaises(DocumentMapError):
            raise DocumentMapError

class TestDocMap(unittest.TestCase):
    def test_load(self):
        dm = DocumentMap('../../mappings', 'article_dir')
        dm.load_mappings()
        self.assertTrue(dm.articles)
        self.assertTrue(dm.folders)
        self.assertTrue(dm.categories)
        self.assertTrue(dm.counters)

        # contents of orginal and copy should be equal
        self.assertEqual(dm.orig_articles, dm.articles)
        self.assertEqual(dm.orig_folders, dm.folders)
        self.assertEqual(dm.orig_categories, dm.categories)

        # contents of orginal and copy should have different mem allocations
        self.assertNotEqual(id(dm.orig_articles), id(dm.articles))
        self.assertNotEqual(id(dm.orig_folders), id(dm.folders))
        self.assertNotEqual(id(dm.orig_categories), id(dm.categories))

        # content of mapping should not be empty and has right keys
        self.assertTrue(dm.counters['article'] in dm.articles.keys())
        self.assertTrue(dm.counters['folder'] in dm.folders.keys())
        self.assertTrue(dm.counters['category'] in dm.categories.keys())
        self.assertEqual(frozenset(dm.counters.keys()), frozenset(['folder', 'article', 'category']))

if __name__ == '__main__':
    unittest.main()