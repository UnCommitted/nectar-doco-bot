from sys import path
path.append('..')

import logging

import unittest
from unittest.mock import patch

from gerrit import GerritAPI
from mock import Response

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

class TestGerritAPI(unittest.TestCase):
    def setUp(self):
        self.gerrit = GerritAPI('gerrit_url', 'project_name', 'username', 'password')

    def test_create_change_successful(self):
        with patch('requests.post') as patched_post:
            patched_post.return_value = Response(201)
            rv = self.gerrit.create_change('change_subject')
            assert patched_post.called
            self.assertIsInstance(rv, tuple)

    def test_create_change_failed(self):
        with patch('requests.post') as patched_post:
            patched_post.return_value = Response(500)
            rv = self.gerrit.create_change('change_subject')
            assert patched_post.called
            self.assertIsInstance(rv, tuple)

if __name__ == '__main__':
    unittest.main()