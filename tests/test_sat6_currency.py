#!/usr/bin/env python2

import sat6_currency
import mock_satellite_api

import collections
import requests
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

    def test_output_csv_empty(self):
        self.assertEqual(sat6_currency.output_csv([]), '')

    def test_output_csv(self):
        self.assertEqual(
            sat6_currency.output_csv(self.output),
            "name,number,colour\n"
            "one,11,green\n"
            "two,22,None\n"
            "three,None,red"
        )

    def test_output_json_empty(self):
        self.assertEqual(sat6_currency.output_json([]), '[]')

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

    def test_output_yaml_empty(self):
        self.assertEqual(sat6_currency.output_yaml([]), '--- []\n')

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

    def test_output_format(self):
        self.assertEqual(
            sat6_currency.output_format('csv'),
            sat6_currency.output_csv
        )
        self.assertEqual(
            sat6_currency.output_format('json'),
            sat6_currency.output_json
        )
        self.assertEqual(
            sat6_currency.output_format('yaml'),
            sat6_currency.output_yaml
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


class TestClass(unittest.TestCase):
    def test_class_url(self):
        config = sat6_currency.SatelliteServerConfig(
            'https://satellite.example.com',
            'Admin',
            'sw0rdfi$h',
        )
        self.assertEqual(config.url, 'https://satellite.example.com')

    def test_class_url_http(self):
        config = sat6_currency.SatelliteServerConfig(
            'http://satellite.example.com',
            'Admin',
            'sw0rdfi$h',
        )
        self.assertEqual(config.url, 'https://satellite.example.com')

    def test_class_url_slash(self):
        config = sat6_currency.SatelliteServerConfig(
            'https://satellite.example.com',
            'Admin',
            'sw0rdfi$h',
        )
        self.assertEqual(config.url, 'https://satellite.example.com')

    def test_class_url_port(self):
        config = sat6_currency.SatelliteServerConfig(
            'https://satellite.example.com:8443',
            'Admin',
            'sw0rdfi$h',
        )
        self.assertEqual(config.url, 'https://satellite.example.com:8443')

    def test_class_url_port_slash(self):
        config = sat6_currency.SatelliteServerConfig(
            'https://satellite.example.com:8443/',
            'Admin',
            'sw0rdfi$h',
        )
        self.assertEqual(config.url, 'https://satellite.example.com:8443')

    def test_class_host(self):
        config = sat6_currency.SatelliteServerConfig(
            'satellite.example.com',
            'Admin',
            'sw0rdfi$h',
        )
        self.assertEqual(config.url, 'https://satellite.example.com')

    def test_class_host_port(self):
        config = sat6_currency.SatelliteServerConfig(
            'satellite.example.com:8443',
            'Admin',
            'sw0rdfi$h',
        )
        self.assertEqual(config.url, 'https://satellite.example.com:8443')


class TestAPI(unittest.TestCase):
    def setUpMockAPI(self):
        self.web_port = mock_satellite_api.get_free_port()
        self.hostname = 'localhost'
        mock_satellite_api.serve_api(port=self.web_port)
        self.url = 'http://{hostname}:{port}'.format(
            hostname=self.hostname, port=self.web_port
        )

    def setUpConfig(self):
        self.config = sat6_currency.SatelliteServerConfig(
            'http://localhost:{}'.format(str(self.web_port)),
            'username',
            'password',
            ssl_verify=False
        )

    def setUp(self):
        self.setUpMockAPI()
        self.setUpConfig()

    def test_get_with_json_bad_host(self):
        with self.assertRaises(requests.ConnectionError):
            sat6_currency.get_with_json(
                self.config,
                'https://satellite.example/bar'
            )

    def test_get_with_json_404(self):
        with self.assertRaises(requests.ConnectionError):
            sat6_currency.get_with_json(
                self.config,
                self.url + '/bar'
            )

    def test_get_with_json_foo(self):
        self.assertEqual(
            sat6_currency.get_with_json(
                self.config,
                self.url + '/foo'
            ),
            [{u'foo': u'bar'}]
        )

    def test_get_with_json_baz(self):
        self.assertEqual(
            sat6_currency.get_with_json(
                self.config,
                self.url + '/baz'
            ),
            [{u'baz': u'qux'}]
        )
