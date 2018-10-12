#!/usr/bin/env python2

import unittest
import sys
import os


class TestImportModule(unittest.TestCase):
    def test_import(self):
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
        import sat6_currency
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
