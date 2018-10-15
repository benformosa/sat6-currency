#!/usr/bin/env python2

import sat6_currency

import unittest


class TestLoadConfig(unittest.TestCase):
    def test_loadconfig_good(self):
        with open('tests/config_good.yaml', 'r') as f:
            (server, username, password) = sat6_currency.loadconfig(f)
            self.assertEqual(server, 'https://example.com/')
            self.assertEqual(username, 'Admin')
            self.assertEqual(password, 'sw0rdfi$h')

    def test_loadconfig_bare(self):
        with open('tests/config_bare.yaml', 'r') as f:
            (server, username, password) = sat6_currency.loadconfig(f)
            self.assertEqual(server, None)
            self.assertEqual(username, None)
            self.assertEqual(password, None)

    def test_loadconfig_empty(self):
        with open('/dev/null', 'r') as f:
            (server, username, password) = sat6_currency.loadconfig(f)
            self.assertEqual(server, None)
            self.assertEqual(username, None)
            self.assertEqual(password, None)


if __name__ == "__main__":
    unittest.main()
