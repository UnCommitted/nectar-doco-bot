from sys import path
path.append('..')

import logging

import unittest
from unittest.mock import patch

import fdbroker

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

class TestBroker(unittest.TestCase):
    def test_startup(self):


if __name__ == '__main__':
    unittest.main()