#!/usr/bin/env python2
"""
Satellite 6 version of 'spacewalk-report system-currency'
"""

from __future__ import print_function
import argparse
import collections
import getpass
import json
import os
import re
import requests
import yaml
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def init(host, user, passwd):
    """Set up global variables."""
    global url, api, katello_api, post_headers, ssl_verify
    global server, username, password
    server = host
    username = user
    password = passwd

    # Satellite specific parameters
    if server.startswith('https://'):
        url = server.strip('/')
    else:
        url = "https://{}".format(server)
    api = url + "/api/"
    katello_api = url + "/katello/api/v2"
    post_headers = {'content-type': 'application/json'}
    ssl_verify = True


def loadconfig(configfile):
    """
    Return a tuple (server, username, password) of values from the
    configuration file.

    Values are None if not specified in the file.
    """
    config = yaml.safe_load(configfile)
    # If the key is present in the config file, attempt to load values
    key = ':foreman'
    try:
        server = config[key][':host']
    except(KeyError):
        pass
    try:
        username = config[key][':username']
    except(KeyError):
        pass
    try:
        password = config[key][':password']
    except(KeyError):
        pass

    return (server, username, password)


def get_with_json(location, json_data):
    """
    Performs a GET and passes the data to the url location
    """
    try:
        result = requests.get(
            location,
            data=json_data,
            auth=(username, password),
            verify=ssl_verify,
            headers=post_headers
        )

    except requests.ConnectionError:
        print("Error: Couldn't connect to the API,"
              " check connection or url '{}'".format(location))
        raise
    if result.ok:
        return result.json()
    else:
        print("Error connecting to '{}'. HTTP Status: {}".format(
            location, str(result.status_code)))
        raise requests.ConnectionError


def output_csv(output):
    """Return list of dicts as string in csv format."""
    if output:
        output_list = []
        [output_list.append(str(k)) for k in output[0].keys()]
        output_list.append(os.linesep)
        for item in output:
            [output_list.append(str(v)) for v in item.values()]
            output_list.append(os.linesep)
        s = ','.join(output_list)
        s = s.replace(',{},'.format(os.linesep), os.linesep)
        s = s.replace(',{}'.format(os.linesep), os.linesep)
        s = s.rstrip(os.linesep)
        return s
    else:
        return ''


def output_yaml(output):
    """Return list of dicts as string in yaml format."""
    return yaml.safe_dump(
        # Convert list of OrderedDict to list of dict
        [dict(item) for item in output],
        explicit_start=True,
        default_flow_style=False,
    )


def output_json(output):
    """Return list of dicts as string in json format."""
    return json.dumps(
        output,
        sort_keys=True,
        indent=2,
        separators=(',', ': '),
    )


OUTPUT_FORMATS = {
    "csv": output_csv,
    "json": output_json,
    "yaml": output_yaml,
}


def output_format(format):
    return OUTPUT_FORMATS[format]


def search_string(queries):
    """
    Return a search query string, given a dict.

    :param queries: A dictionary, containing key/value pairs to search for
    """

    s = ','.join("{}={}".format(k, v) for (k, v) in queries.iteritems())
    return "?search=" + s


def search_queries(sstring):
    """
    Return a dict, given a search query string.

    :param queries: A string, in the format [?search=]key=value[,key=value]*
    """
    sstring = re.sub(r'^\?search=', '', sstring, flags=re.IGNORECASE)

    if sstring:
        d = dict(item.split("=") for item in sstring.split(","))
    else:
        d = {}
    return d


# Multiply factors according to "spacewalk-report system-currency"
FACTOR_CRI = 32
FACTOR_IMP = 16
FACTOR_MOD = 8  # Used for security errata in score_simple
FACTOR_LOW = 4
FACTOR_BUG = 2
FACTOR_ENH = 1


def score_simple(sec, bug, enh):
    """Calculate a score based on number of outstanding errata."""
    return (
        (sec or 0) * FACTOR_MOD +
        (bug or 0) * FACTOR_BUG +
        (enh or 0) * FACTOR_ENH
    )


def score_advanced(cri, imp, mod, low, bug, enh):
    """Calculate a score based on number of outstanding errata."""
    return (
        (cri or 0) * FACTOR_CRI +
        (imp or 0) * FACTOR_IMP +
        (mod or 0) * FACTOR_MOD +
        (low or 0) * FACTOR_LOW +
        (bug or 0) * FACTOR_BUG +
        (enh or 0) * FACTOR_ENH
    )


def simple_currency(search=""):
    """
    Simple form of the system currency report.

    Return a list of dicts.
    """

    output = []

    # Get all hosts (alter if you have more than 10000 hosts)
    hosts = get_with_json(
        "{}hosts{}".format(api, search),
        json.dumps({"per_page": "10000"})
    )["results"]

    for host in hosts:
        # Check if host is registered with subscription-manager
        # (unregistered hosts lack these values and are skipped)
        if not ("content_facet_attributes" in host and
                host["content_facet_attributes"]["errata_counts"]):
            continue

        host_data = collections.OrderedDict([
            ("system_id", host["id"]),
            ("org_name", host["organization_name"]),
            ("name", host["name"]),
            ("security", None),
            ("bug", None),
            ("enhancement", None),
            ("score", None),
            ("content_view", None),
            ("content_view_publish_date", None),
            ("lifecycle_environment", None),
            ("subscription_os_release", None),
            ("os_release", None),
            ("arch", None),
            ("subscription_status", None),
            ("comment", host["comment"]),
        ])

        # Get each number of different kinds of erratas
        host_data["security"] = (
            host["content_facet_attributes"]["errata_counts"]["security"])
        host_data["bug"] = (
            host["content_facet_attributes"]["errata_counts"]["bugfix"])
        host_data["enhancement"] = (
            host["content_facet_attributes"]["errata_counts"]["enhancement"])
        host_data["content_view"] = (
            host["content_facet_attributes"]["content_view"]["name"])
        content_view_id = (
            host["content_facet_attributes"]["content_view"]["id"])
        host_data["lifecycle_environment"] = (
            host["content_facet_attributes"]["lifecycle_environment"]["name"])
        lifecycle_environment_id = (
            host["content_facet_attributes"]["lifecycle_environment"]["id"])
        host_data["subscription_os_release"] = (
            host["subscription_facet_attributes"]["release_version"])
        host_data["arch"] = host["architecture_name"]
        host_data["subscription_status"] = (
            host["subscription_status_label"])
        host_data["os_release"] = host["operatingsystem_name"]

        content_view = get_with_json(
            "{}/content_views/{}/content_view_versions?"
            "environment_id={}".format(
                katello_api,
                str(content_view_id),
                str(lifecycle_environment_id)
            ),
            json.dumps({"per_page": "10000"})
        )["results"]

        host_data["content_view_publish_date"] = (
            content_view[0]["created_at"])

        # Calculate weighted score
        host_data["score"] = score_simple(
            host_data["security"],
            host_data["bug"],
            host_data["enhancement"]
        )
        output.append(host_data)
    return output


def advanced_currency(search):
    """
    Advanced form of the system currency report.

    Return a list of dicts.
    """

    output = []

    # Get all hosts (for more than 10000 hosts, this will take a long time)
    hosts = get_with_json(
        "{}hosts{}".format(api, search),
        json.dumps({"per_page": "10000"})
    )["results"]

    for host in hosts:
        host_data = collections.OrderedDict([
            ("system_id", host["id"]),
            ("org_name", host["organization_name"]),
            ("name", host["name"]),
            ("critical", 0),
            ("important", 0),
            ("moderate", 0),
            ("low", 0),
            ("bug", 0),
            ("enhancement", 0),
            ("score", None),
            ("content_view", None),
            ("content_view_publish_date", None),
            ("lifecycle_environment", None),
            ("subscription_os_release", None),
            ("os_release", host["operatingsystem_name"]),
            ("arch", host["architecture_name"]),
            ("subscription_status", None),
            ("comment", host["comment"]),
        ])

        # Get all errata for each host
        erratas = get_with_json(
            "{}hosts/{}/errata".format(api, str(host["id"])),
            json.dumps({"per_page": "10000"})
        )

        # Check if host is registered with subscription-manager
        # (unregistered hosts lack these values and are skipped)
        if "results" in erratas:
            # Check if host have any errrata at all
            if not ("total" in erratas and
                    "content_facet_attributes" in host and
                    "subscription_facet_attributes" in host):
                continue

            host_data["content_view"] = (
                host["content_facet_attributes"]["content_view"]["name"])
            content_view_id = (
                host["content_facet_attributes"]["content_view"]["id"])
            host_data["lifecycle_environment"] = (
                host["content_facet_attributes"]["lifecycle_environment"]["name"])  # noqa
            lifecycle_environment_id = (
                host["content_facet_attributes"]["lifecycle_environment"]["id"])  # noqa
            host_data["subscription_os_release"] = (
                host["subscription_facet_attributes"]["release_version"])
            host_data["subscription_status"] = (
                host["subscription_status_label"])

            content_view = get_with_json(
                "{}/content_views/{}/content_view_versions?"
                "environment_id={}".format(
                    katello_api,
                    str(content_view_id),
                    str(lifecycle_environment_id)
                ),
                json.dumps({"per_page": "10000"})
            )["results"]

            host_data["content_view_publish_date"] = (
                content_view[0]["created_at"])

            # Go through each errata
            for errata in erratas["results"]:
                # If it is a security errata, check the severity
                if errata["type"] == "security":
                    if errata["severity"] == "Critical":
                        host_data["critical"] += 1
                    if errata["severity"] == "Important":
                        host_data["important"] += 1
                    if errata["severity"] == "Moderate":
                        host_data["moderate"] += 1
                    if errata["severity"] == "Low":
                        host_data["low"] += 1

                if errata["type"] == "enhancement":
                    host_data["enhancement"] += 1
                if errata["type"] == "bugfix":
                    host_data["bug"] += 1

            # Calculate weighted score
            host_data["score"] = score_advanced(
                host_data["critical"],
                host_data["important"],
                host_data["moderate"],
                host_data["low"],
                host_data["bug"],
                host_data["enhancement"]
            )
            output.append(host_data)
    return output


def library_currency(org, env, cv, search=""):
    """
    Advanced form of the system currency report, with more errata detail.

    Return a Tuple of lists of dicts: (output, available, applicable)
    output: list of hosts with currency report data
    available: list of errata which are available
    applicable: list of errata which are applicable
    """

    if org is None:
        raise RuntimeError("Organization must be specified for Library report")

    output = []
    available = []
    applicable = []

    # Red Hat errata URL
    RH_URL = "https://access.redhat.com/errata/"

    # Find organization
    organization = get_with_json(
        "{}/organizations/?Search={}".format(katello_api, org),
        json.dumps({"per_page": "10000"})
    )["results"]
    organization_id = organization[0]["id"]
    # print str(organization_id)

    # Find lifecycle_environment
    lifecycle_environment_compare = get_with_json(
        "{}/organizations/{}/environments?name={}".format(
            katello_api,
            str(organization_id),
            env
        ),
        json.dumps({"per_page": "10000"})
    )["results"]
    lifecycle_environment_compare_id = lifecycle_environment_compare[0]["id"]
    # print str(lifecycle_environment_compare_id)

    # Find content view
    content_view_compare = get_with_json(
        "{}/organizations/{}/content_views?name={}".format(
            katello_api,
            str(organization_id),
            cv
        ),
        json.dumps({"per_page": "10000"})
    )["results"]
    content_view_compare_id = content_view_compare[0]["id"]
    # print str(content_view_compare_id)

    # Get all hosts (for more than 10000 hosts, this will take a long time)
    hosts = get_with_json(
        "{}hosts{}".format(api, search),
        json.dumps({"per_page": "10000"})
    )["results"]

    for host in hosts:
        host_data = collections.OrderedDict([
            ("system_id", host["id"]),
            ("org_name", host["organization_name"]),
            ("name", host["name"]),
            ("total_available_security", 0),
            ("critical", 0),
            ("important", 0),
            ("moderate", 0),
            ("low", 0),
            ("bug", 0),
            ("enhancement", 0),
            ("score", 0),
            ("total_applicable_security", 0),
            ("applicable_critical", 0),
            ("applicable_important", 0),
            ("applicable_moderate", 0),
            ("applicable_low", 0),
            ("applicable_bug", 0),
            ("applicable_enhancement", 0),
            ("applicable_score", 0),
            ("content_view", None),
            ("content_view_publish_date", None),
            ("lifecycle_environment", None),
            ("subscription_os_release", None),
            ("os_release", host["operatingsystem_name"]),
            ("arch", host["architecture_name"]),
            ("subscription_status", None),
            ("comment", host["comment"]),
        ])

        # Get all errata for each host
        erratas = get_with_json(
            "{}hosts/{}/errata".format(
                api,
                str(host["id"]
                    )),
            json.dumps({"per_page": "10000"})
        )
        applicable_erratas = get_with_json(
            "{}hosts/{}/errata?environment_id={}&content_view_id={}".format(
                api,
                str(host["id"]),
                str(lifecycle_environment_compare_id),
                str(content_view_compare_id)
            ),
            json.dumps({"per_page": "10000"})
        )

        # Check if host is registered with subscription-manager
        # (unregistered hosts lack these values and are skipped)
        if "results" in erratas:
            # Check if host have any errrata at all
            if not ("total" in erratas and
                    "content_facet_attributes" in host and
                    "subscription_facet_attributes" in host):
                continue

            host_data["content_view"] = (
                host["content_facet_attributes"]["content_view"]["name"])
            content_view_id = (
                host["content_facet_attributes"]["content_view"]["id"])
            host_data["lifecycle_environment"] = (
                host["content_facet_attributes"]["lifecycle_environment"]["name"])  # noqa
            lifecycle_environment_id = (
                host["content_facet_attributes"]["lifecycle_environment"]["id"])  # noqa
            host_data["subscription_os_release"] = (
                host["subscription_facet_attributes"]["release_version"])
            host_data["subscription_status"] = (
                host["subscription_status_label"])

            content_view = get_with_json(
                "{}/content_views/{}/content_view_versions?"
                "environment_id={}".format(
                    katello_api,
                    str(content_view_id),
                    str(lifecycle_environment_id)
                ),
                json.dumps({"per_page": "10000"})
            )["results"]

            host_data["content_view_publish_date"] = (
                content_view[0]["created_at"])

            # Go through each errata that is available
            for errata in erratas["results"]:

                # If it is a security errata, check the severity
                if errata["type"] == "security":
                    host_data["total_available_security"] += 1
                    if errata["severity"] == "Critical":
                        host_data["critical"] += 1
                    if errata["severity"] == "Important":
                        host_data["important"] += 1
                    if errata["severity"] == "Moderate":
                        host_data["moderate"] += 1
                    if errata["severity"] == "Low":
                        host_data["low"] += 1

                if errata["type"] == "enhancement":
                    host_data["enhancement"] += 1
                if errata["type"] == "bugfix":
                    host_data["bug"] += 1

                # Delete any commas from the errata title
                # eg: https://access.redhat.com/errata/RHSA-2017:0817
                errata["title"] = errata["title"].replace(',', '')
                available.append(collections.OrderedDict([
                    ("system_id", str(host["id"])),
                    ("org_name", str(host["organization_name"])),
                    ("name", host["name"]),
                    ("state", "Available"),
                    ("errata_id", str(errata["errata_id"])),
                    ("issued", str(errata["issued"])),
                    ("updated", str(errata["updated"])),
                    ("severity", str(errata["severity"])),
                    ("type", str(errata["type"])),
                    ("reboot_suggested", str(errata["reboot_suggested"])),
                    ("title", str(errata["title"])),
                    ("further_info",
                     "{}{}".format(RH_URL, str(errata["errata_id"]))),
                ]))

            # Go through each errata that is applicable (in the library)
            for errata in applicable_erratas["results"]:

                # If it is a security errata, check the severity
                if errata["type"] == "security":
                    host_data["total_applicable_security"] += 1
                    if errata["severity"] == "Critical":
                        host_data["applicable_critical"] += 1
                    if errata["severity"] == "Important":
                        host_data["applicable_important"] += 1
                    if errata["severity"] == "Moderate":
                        host_data["applicable_moderate"] += 1
                    if errata["severity"] == "Low":
                        host_data["applicable_low"] += 1

                if errata["type"] == "enhancement":
                    host_data["applicable_enhancement"] += 1
                if errata["type"] == "bugfix":
                    host_data["applicable_bug"] += 1

                # Delete any commas from the errata title
                # eg: https://access.redhat.com/errata/RHSA-2017:0817
                errata["title"] = errata["title"].replace(',', '')

                applicable.append(collections.OrderedDict([
                    ("system_id", str(host["id"])),
                    ("org_name", str(host["organization_name"])),
                    ("name", host["name"]),
                    ("state", "Applicable"),
                    ("errata_id", str(errata["errata_id"])),
                    ("issued", str(errata["issued"])),
                    ("updated", str(errata["updated"])),
                    ("severity", str(errata["severity"])),
                    ("type", str(errata["type"])),
                    ("reboot_suggested", str(errata["reboot_suggested"])),
                    ("title", str(errata["title"])),
                    ("further_info",
                     "{}{}".format(RH_URL, str(errata["errata_id"]))),
                ]))

            # Calculate weighted score
            host_data["score"] = score_advanced(
                host_data["critical"],
                host_data["important"],
                host_data["moderate"],
                host_data["low"],
                host_data["bug"],
                host_data["enhancement"]
            )
            host_data["applicable_score"] = score_advanced(
                host_data["applicable_critical"],
                host_data["applicable_important"],
                host_data["applicable_moderate"],
                host_data["applicable_low"],
                host_data["applicable_bug"],
                host_data["applicable_enhancement"]
            )
            output.append(host_data)
    return (output, available, applicable)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Satellite 6 version of 'spacewalk-report system-currency'"
    )
    parser.add_argument(
        "-a", "--advanced",
        action="store_true",
        default=False,
        help="Use this flag if you want to divide security errata by severity."
        " Note: this will reduce performance if this script significantly."
    )
    parser.add_argument(
        "-f", "--config",
        type=argparse.FileType(mode='r'),
        nargs='?',
        help="Hammer CLI config file (defaults to ~/.hammer/cli_config.yml",
        const=os.path.expanduser('~/.hammer/cli_config.yml')
    )
    parser.add_argument(
        "-n", "--server",
        type=str.lower,
        help="Satellite server"
    )
    parser.add_argument(
        "-u", "--username",
        type=str,
        help="Username to access Satellite"
    )
    parser.add_argument(
        "-p", "--password",
        type=str,
        help="Password to access Satellite."
        " The user will be asked interactively if password is not provided."
    )
    parser.add_argument(
        "-s", "--search",
        type=str,
        required=False,
        help="Search string for host."
        "( like ?search=lifecycle_environment=Test",
        default=('')
    )
    parser.add_argument(
        "-l", "--library",
        action="store_true",
        required=False,
        help="Use this flag to also report on Library Synced Content AND"
        " to divide security errata by severity."
        " Note: this will reduce performance of this script significantly."
        " Use with -o, -e and -c options"
    )
    parser.add_argument(
        "-o", "--organization",
        type=str,
        default=None,
        required=False,
        help="Organization to use when using the '-l' option"
    )
    parser.add_argument(
        "-c", "--contentview",
        type=str,
        required=False,
        default="Default Organization View",
        help="Content View to use using the '-l' option."
        " Default: Default Organization View"
    )
    parser.add_argument(
        "-e", "--environment",
        type=str,
        required=False,
        default="Library",
        help="Environment to use with the '-l' option. Default: Library"
    )
    parser.add_argument(
        "--output",
        choices=OUTPUT_FORMATS.keys(),
        type=str,
        required=False,
        default="csv",
        help="Output format"
    )
    args = parser.parse_args()

    # If config option specified, read Hammer CLI config file
    if args.config is not None:
        (server, username, password) = loadconfig(args.config)

    # Values specified on the commandline take precendence over config file
    if args.server is not None:
        server = args.server
    if args.username is not None:
        username = args.username
    if args.password is not None:
        password = args.password

    if server is None:
        raise ValueError("Server was not specified")
    if username is None:
        raise ValueError("Username was not specified")
    if password is None:
        password = getpass.getpass()

    init(server, username, password)

    search_dict = search_queries(args.search)
    if args.organization:
        search_dict['organization'] = args.organization
    search_string = search_string(search_dict)

    output_function = output_format(args.output)

    filename_available = "available." + args.output
    filename_applicable = "applicable." + args.output

    if args.advanced:
        output = advanced_currency(search_string)
    elif args.library:
        (
            output,
            available,
            applicable
        ) = library_currency(
            args.organization,
            args.environment,
            args.contentview,
            search_string
        )

        if available:
            with open(filename_available, 'w') as f:
                print(output_function(available), file=f)
        if applicable:
            with open(filename_applicable, 'w') as f:
                print(output_function(applicable), file=f)
    else:
        output = simple_currency(search_string)

    print(output_function(output))
