from sys import path
path.append('..')

import logging

import unittest
from unittest.mock import patch

from gerrit import GerritAPI

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

class Response:
    """A mock requests.response"""
    def __init__(self, code):
        self.status_code = code
        self.headers = {}
        self.text = """)]}'{"id":"NeCTAR-RC%2Fnectarcloud-tier0doco~master~I2109f1dffb4da78520296e8dadb71d96a40f786b","project":"NeCTAR-RC/nectarcloud-tier0doco","branch":"master","hashtags":[],"change_id":"I2109f1dffb4da78520296e8dadb71d96a40f786b","subject":"brokerupdate-2015-07-16-12:24:31","status":"DRAFT","created":"2015-07-16 02:54:30.611000000","updated":"2015-07-16 02:54:30.611000000","mergeable":true,"insertions":0,"deletions":0,"_number":2951,"owner":{"_account_id":1000127}}"""
    def json(self):
        return None

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