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


class TestSearchString(unittest.TestCase):
    def test_search_string_empty(self):
        self.assertEqual(
            sat6_currency.search_string({}),
            "?search="
        )

    def test_search_string_one(self):
        self.assertEqual(
            sat6_currency.search_string({
                "key1": "value1",
            }),
            "?search=key1=value1"
        )

    def test_search_string_two(self):
        self.assertEqual(
            sat6_currency.search_string(
                collections.OrderedDict([
                    ("key1", "value1"),
                    ("key2", "value2"),
                ])
            ),
            "?search=key1=value1,key2=value2"
        )


class TestSearchQueries(unittest.TestCase):
    def test_search_queries_empty(self):
        self.assertEqual(sat6_currency.search_queries(""), {})

    def test_search_queries_noquery(self):
        self.assertEqual(
            sat6_currency.search_queries("?Search="),
            {}
        )

    def test_search_queries_one(self):
        self.assertEqual(
            sat6_currency.search_queries("?search=key1=value1"),
            {"key1": "value1"}
        )

    def test_search_queries_two(self):
        self.assertEqual(
            sat6_currency.search_queries("?search=key1=value1,key2=value2"),
            {
                "key1": "value1",
                "key2": "value2",
            }
        )

    def test_search_queries_emptyvalue(self):
        self.assertEqual(
            sat6_currency.search_queries("?search=key1="),
            {"key1": ""}
        )

    def test_search_queries_novalue(self):
        self.assertEqual(
            sat6_currency.search_queries("?search=key1"),
            {"key1": ""}
        )


class TestScore(unittest.TestCase):
    def test_score_simple_none(self):
        self.assertEqual(
            sat6_currency.score_simple(None, None, None),
            0
        )

    def test_score_simple(self):
        self.assertEqual(
            sat6_currency.score_simple(1, 1, 1),
            8 + 2 + 1
        )

    def test_score_advanced_none(self):
        self.assertEqual(
            sat6_currency.score_advanced(None, None, None, None, None, None),
            0
        )

    def test_score_advanced(self):
        self.assertEqual(
            sat6_currency.score_advanced(1, 1, 1, 1, 1, 1),
            32 + 16 + 8 + 4 + 2 + 1
        )


if __name__ == "__main__":
    unittest.main()
