#!/usr/bin/env python2

import unittest


class TestImportModule(unittest.TestCase):
    def test_import(self):
        import sat6_currency
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
