#!/usr/bin/env python2

import sat6_currency

import collections
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


class TestOutput(unittest.TestCase):
    def setUp(self):
        self.output = [
            collections.OrderedDict([
                ('name', 'one'),
                ('number', 11),
                ('colour', 'green'),
            ]),
            collections.OrderedDict([
                ('name', 'two'),
                ('number', 22),
                ('colour', None),
            ]),
            collections.OrderedDict([
                ('name', 'three'),
                ('number', None),
                ('colour', 'red'),
            ]),
        ]

    def test_output_csv(self):
        self.assertEqual(
            sat6_currency.output_csv(self.output),
            "name,number,colour\n"
            "one,11,green\n"
            "two,22,None\n"
            "three,None,red"
        )

    def test_output_json(self):
        self.assertEqual(
            sat6_currency.output_json(self.output),
            '[\n'
            '  {\n'
            '    "colour": "green",\n'
            '    "name": "one",\n'
            '    "number": 11\n'
            '  },\n'
            '  {\n'
            '    "colour": null,\n'
            '    "name": "two",\n'
            '    "number": 22\n'
            '  },\n'
            '  {\n'
            '    "colour": "red",\n'
            '    "name": "three",\n'
            '    "number": null\n'
            '  }\n'
            ']'
        )

    def test_output_yaml(self):
        self.assertEqual(
            sat6_currency.output_yaml(self.output),
            "---\n"
            "- colour: green\n"
            "  name: one\n"
            "  number: 11\n"
            "- colour: null\n"
            "  name: two\n"
            "  number: 22\n"
            "- colour: red\n"
            "  name: three\n"
            "  number: null\n"
        )


if __name__ == "__main__":
    unittest.main()
