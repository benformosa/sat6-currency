#!/usr/bin/env python2

import sat6_currency
import mock_satellite_api

import collections
import os
import requests
import unittest


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        self.directory = os.path.abspath(os.path.dirname(__file__))

    def test_loadconfig_good(self):
        with open(os.path.join(self.directory, 'config_good.yaml'), 'r') as f:
            (server, username, password) = sat6_currency.loadconfig(f)
            self.assertEqual(server, 'https://example.com/')
            self.assertEqual(username, 'Admin')
            self.assertEqual(password, 'sw0rdfi$h')

    def test_loadconfig_bare(self):
        with open(os.path.join(self.directory, 'config_bare.yaml'), 'r') as f:
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


class TestCaseWithMock(unittest.TestCase):
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


class TestAPI(TestCaseWithMock):
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

    def test_get_with_json_baz(self):
        self.assertEqual(
            sat6_currency.get_with_json(
                self.config,
                self.url + '/baz.json'
            ),
            [{u'baz': u'qux'}]
        )


class TestSimpleCurrency(TestCaseWithMock):
    def test_simple_currency(self):
        self.assertEqual(
            sat6_currency.simple_currency(self.config),
            [collections.OrderedDict([
                ('system_id', 5),
                ('org_name', u'ORG'),
                ('name', u'dev1.example.com'),
                ('security', 6),
                ('bug', 5),
                ('enhancement', 2),
                ('score', 60),
                ('content_view', u'RHEL 7 DevTools'),
                ('content_view_publish_date', u'2018-10-09 21:31:44 UTC'),
                ('lifecycle_environment', u'Development'),
                ('subscription_os_release', u'7Server'),
                ('os_release', u'RedHat 7.5'),
                ('arch', u'x86_64'),
                ('subscription_status', u'Fully entitled'),
                ('comment', u'Development machine')
            ])]
        )


class TestAdvancedCurrency(TestCaseWithMock):
    def test_advanced_currency(self):
        self.assertEqual(
            sat6_currency.advanced_currency(self.config),
            [collections.OrderedDict([
                ('system_id', 5),
                ('org_name', u'ORG'),
                ('name', u'dev1.example.com'),
                ("critical", 1),
                ("important", 2),
                ("moderate", 2),
                ("low", 1),
                ("bug", 5),
                ("enhancement", 2),
                ('score', 96),
                ('content_view', u'RHEL 7 DevTools'),
                ('content_view_publish_date', u'2018-10-09 21:31:44 UTC'),
                ('lifecycle_environment', u'Development'),
                ('subscription_os_release', u'7Server'),
                ('os_release', u'RedHat 7.5'),
                ('arch', u'x86_64'),
                ('subscription_status', u'Fully entitled'),
                ('comment', u'Development machine')
            ])]
        )


class TestLibraryCurrency(TestCaseWithMock):
    def setUp(self):
        super(TestLibraryCurrency, self).setUp()
        self.output = [collections.OrderedDict([
            ('system_id', 5),
            ('org_name', u'ORG'),
            ('name', u'dev1.example.com'),
            ("total_available_security", 6),
            ("critical", 1),
            ("important", 2),
            ("moderate", 2),
            ("low", 1),
            ("bug", 5),
            ("enhancement", 2),
            ('score', 96),
            ("total_applicable_security", 6),
            ("applicable_critical", 1),
            ("applicable_important", 2),
            ("applicable_moderate", 2),
            ("applicable_low", 1),
            ("applicable_bug", 5),
            ("applicable_enhancement", 2),
            ("applicable_score", 96),
            ('content_view', u'RHEL 7 DevTools'),
            ('content_view_publish_date', u'2018-10-09 21:31:44 UTC'),
            ('lifecycle_environment', u'Development'),
            ('subscription_os_release', u'7Server'),
            ('os_release', u'RedHat 7.5'),
            ('arch', u'x86_64'),
            ('subscription_status', u'Fully entitled'),
            ('comment', u'Development machine')
        ])]

        self.available = [
            collections.OrderedDict([
                ("system_id", '5'),
                ("org_name", 'ORG'),
                ("name", 'dev1.example.com'),
                ("state", "Available"),
                ("errata_id", 'RHSA-2018:2942'),
                ("issued", '2018-10-17'),
                ("updated", '2018-10-17'),
                ("severity", 'Critical'),
                ("type", 'security'),
                ("reboot_suggested", 'False'),
                ("title", 'Critical: java-1.8.0-openjdk security update'),
                ("further_info", 'https://access.redhat.com/errata/RHSA-2018:2942'),  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHBA-2018:2941'),
                ('issued', '2018-10-17'),
                ('updated', '2018-10-17'),
                ('severity', 'None'),
                ('type', 'bugfix'),
                ('reboot_suggested', 'False'),
                ('title', 'virtio-win bug fix update'),
                ('further_info', 'https://access.redhat.com/errata/RHBA-2018:2941')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHSA-2018:2921'),
                ('issued', '2018-10-16'),
                ('updated', '2018-10-16'),
                ('severity', 'Important'),
                ('type', 'security'),
                ('reboot_suggested', 'False'),
                ('title', 'Important: tomcat security update'),
                ('further_info', 'https://access.redhat.com/errata/RHSA-2018:2921')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHSA-2018:2918'),
                ('issued', '2018-10-16'),
                ('updated', '2018-10-16'),
                ('severity', 'Important'),
                ('type', 'security'),
                ('reboot_suggested', 'False'),
                ('title', 'Important: ghostscript security update'),
                ('further_info', 'https://access.redhat.com/errata/RHSA-2018:2918')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHBA-2018:2914'),
                ('issued', '2018-10-11'),
                ('updated', '2018-10-11'),
                ('severity', 'None'),
                ('type', 'bugfix'),
                ('reboot_suggested', 'False'),
                ('title', 'Satellite Tools 6.3.4 Async Bug Fix Update'),
                ('further_info', 'https://access.redhat.com/errata/RHBA-2018:2914')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHEA-2018:2903'),
                ('issued', '2018-10-10'),
                ('updated', '2018-10-10'),
                ('severity', 'None'),
                ('type', 'enhancement'),
                ('reboot_suggested', 'False'),
                ('title', 'new package: kmod-oracleasm'),
                ('further_info', 'https://access.redhat.com/errata/RHEA-2018:2903')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHBA-2018:2894'),
                ('issued', '2018-10-09'),
                ('updated', '2018-10-09'),
                ('severity', 'None'),
                ('type', 'bugfix'),
                ('reboot_suggested', 'False'),
                ('title', 'mailx bug fix update'),
                ('further_info', 'https://access.redhat.com/errata/RHBA-2018:2894')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHBA-2018:2899'),
                ('issued', '2018-10-09'),
                ('updated', '2018-10-09'),
                ('severity', 'None'),
                ('type', 'bugfix'),
                ('reboot_suggested', 'False'),
                ('title', 'ypserv bug fix update'),
                ('further_info', 'https://access.redhat.com/errata/RHBA-2018:2899')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHBA-2018:2893'),
                ('issued', '2018-10-09'),
                ('updated', '2018-10-09'),
                ('severity', 'None'),
                ('type', 'bugfix'),
                ('reboot_suggested', 'False'),
                ('title', 'gcc-libraries bug fix and enhancement update'),
                ('further_info', 'https://access.redhat.com/errata/RHBA-2018:2893')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHSA-2018:2898'),
                ('issued', '2018-10-09'),
                ('updated', '2018-10-09'),
                ('severity', 'Moderate'),
                ('type', 'security'),
                ('reboot_suggested', 'False'),
                ('title', 'Moderate: nss security update'),
                ('further_info', 'https://access.redhat.com/errata/RHSA-2018:2898')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHSA-2018:2892'),
                ('issued', '2018-10-09'),
                ('updated', '2018-10-09'),
                ('severity', 'Moderate'),
                ('type', 'security'),
                ('reboot_suggested', 'False'),
                ('title', 'Moderate: glusterfs security bug fix and enhancement update'),  # noqa
                ('further_info', 'https://access.redhat.com/errata/RHSA-2018:2892')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHEA-2018:2890'),
                ('issued', '2018-10-09'),
                ('updated', '2018-10-09'),
                ('severity', 'None'),
                ('type', 'enhancement'),
                ('reboot_suggested', 'False'),
                ('title', 'Red Hat Enterprise Linux 6.10 Container Image Update'),  # noqa
                ('further_info',
                 'https://access.redhat.com/errata/RHEA-2018:2890')  # noqa
            ]),
            collections.OrderedDict([
                ('system_id', '5'),
                ('org_name', 'ORG'),
                ('name', u'dev1.example.com'),
                ('state', 'Available'),
                ('errata_id', 'RHSA-2018:9999'),
                ('issued', '2018-10-09'),
                ('updated', '2018-10-09'),
                ('severity', 'Low'),
                ('type', 'security'),
                ('reboot_suggested', 'False'),
                ('title', 'Low: fake update'),
                ('further_info', 'https://access.redhat.com/errata/RHSA-2018:9999')  # noqa
            ]),
        ]

        self.applicable = []
        for errata in self.available:
            c = errata.copy()
            c.update({"state": "Applicable"})
            self.applicable.append(c)

    def test_library_currency(self):
        (
            output,
            available,
            applicable
        ) = sat6_currency.library_currency(
            self.config,
            'ORG',
            'Library',
            'Default Organization View'
        )

        self.assertEqual(
            output,
            self.output
        )
        self.assertEqual(
            available,
            self.available
        )
        self.assertEqual(
            applicable,
            self.applicable
        )

    def test_library_currency_noneorg(self):
        """Test the library_currency report when Org is specified as None"""
        (
            output,
            available,
            applicable
        ) = sat6_currency.library_currency(
            self.config,
            None,
            'Library',
            'Default Organization View'
        )

        self.assertEqual(
            output,
            self.output
        )
        self.assertEqual(
            available,
            self.available
        )
        self.assertEqual(
            applicable,
            self.applicable
        )
