from sys import path
path.append('..')

import logging

import unittest
from unittest.mock import patch

from docmap.freshdesk import FreshDesk

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

class Response:
    """A mock requests.response"""
    def __init__(self, code):
        self.status_code = code
    def json(self):
        return None
    def headers(self):
        return {}

class TestFreshDesk(unittest.TestCase):
    def setUp(self):
        self.fd = FreshDesk('api_url', 'api_token')

    def test_get_solution_categories(self):
        with patch('requests.get') as patched_get:
            self.fd.get_solution_categories()
            patched_get.assert_called_with('api_url/solution/categories.json', auth=('api_token', 'X'))

    def test_create_category_successful(self):
        with patch('requests.post') as patched_post:
            patched_post.return_value = Response(201)
            self.fd.create_category({'title':'cat'})
            assert patched_post.called

    def test_create_category_failed(self):
        with patch('requests.post') as patched_post:
            patched_post.return_value = Response(500)
            self.fd.create_category({'title':'cat'})
            assert patched_post.called

if __name__ == '__main__':
    unittest.main()