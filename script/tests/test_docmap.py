from sys import path
path.append('..')

import unittest
from unittest.mock import patch
from unittest.mock import create_autospec

from docmap import DocumentMap
from docmap.freshdesk import FreshDeskDocumentMap

class TestDocMapCodeChange(unittest.TestCase):
    def test_load_skip_loadX(self):
        with patch('docmap.DocumentMap.load_articles'),\
         patch('docmap.DocumentMap.load_folders'), \
         patch('docmap.DocumentMap.load_categories'), \
         patch('docmap.DocumentMap.load_counters'):
            x = DocumentMap('../../mappings', 'article_dir')
            x.load_mappings()
        self.assertIsNot(x.orig_articles, {})
        self.assertTrue(x.xcounters)

    def test_load(self):
        x = DocumentMap('../../mappings', 'article_dir')
        x.load_mappings()
        self.assertTrue(x.articles)
        self.assertTrue(x.folders)
        self.assertTrue(x.categories)
        self.assertTrue(x.counters)

        self.assertTrue(x.xarticles)
        self.assertTrue(x.xfolders)
        self.assertTrue(x.xcategories)
        self.assertTrue(x.xcounters)

        # replacements should be equal to those to be replaced
        self.assertEqual(x.xarticles, x.articles)
        self.assertEqual(x.xfolders, x.folders)
        self.assertEqual(x.xcategories, x.categories)
        self.assertEqual(x.xcounters, x.counters)
        self.assertEqual(x.xorig_articles, x.orig_articles)
        self.assertEqual(x.xorig_folders, x.orig_folders)
        self.assertEqual(x.xorig_categories, x.orig_categories)

        # contents of orginal and copy should be equal
        self.assertEqual(x.xorig_articles, x.xarticles)
        self.assertEqual(x.xorig_folders, x.xfolders)
        self.assertEqual(x.xorig_categories, x.xcategories)

        # contents of orginal and copy should have different mem allocations
        self.assertNotEqual(id(x.xorig_articles), id(x.xarticles))
        self.assertNotEqual(id(x.xorig_folders), id(x.xfolders))
        self.assertNotEqual(id(x.xorig_categories), id(x.xcategories))


class TestDocMap(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()