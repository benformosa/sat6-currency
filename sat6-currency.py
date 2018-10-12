#!/usr/bin/env python2
"""
Satellite 6 version of 'spacewalk-report system-currency'
"""

import argparse
import collections
import csv
import getpass
import json
import os
import re
import requests
import sys
import yaml
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def init(server):
    """Set up global variables."""
    global url, api, katello_api, post_headers, ssl_verify

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

    except requests.ConnectionError, e:
        print("{} Couldn't connect to the API,"
              " check connection or url".format(location))
        print(e)
        sys.exit(1)
    if result.ok:
        return result.json()
    else:
        print(" Error connecting to '{}'. HTTP Status: {}".format(
            location, str(result.status_code)))
        sys.exit(1)


def output_csv(output):
    """Print list of dicts to STDOUT in csv format."""
    if output:
        fieldnames = output[0].keys()
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output)


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

    # Multiply factors
    factor_sec = 8
    factor_bug = 2
    factor_enh = 1

    for host in hosts:
        # Check if host is registered with subscription-manager
        # (unregistered hosts lack these values and are skipped)
        if (
                "content_facet_attributes" in host and
                host["content_facet_attributes"]["errata_counts"]
        ):
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
            host_data["security"] = host[
                "content_facet_attributes"]["errata_counts"]["security"]
            host_data["bug"] = host[
                "content_facet_attributes"]["errata_counts"]["bugfix"]
            host_data["enhancement"] = host[
                "content_facet_attributes"]["errata_counts"]["enhancement"]
            host_data["content_view"] = host[
                "content_facet_attributes"]["content_view"]["name"]
            content_view_id = host[
                "content_facet_attributes"]["content_view"]["id"]
            host_data["lifecycle_environment"] = host[
                "content_facet_attributes"]["lifecycle_environment"]["name"]
            lifecycle_environment_id = host[
                "content_facet_attributes"]["lifecycle_environment"]["id"]
            host_data["subscription_os_release"] = host[
                "subscription_facet_attributes"]["release_version"]
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
            if (
                    host_data["security"] is None or
                    host_data["bug"] is None or
                    host_data["enhancement"] is None
            ):
                host_data["score"] = 0
            else:
                # Calculate weighted score
                host_data["score"] = (
                    host_data["security"] * factor_sec +
                    host_data["bug"] * factor_bug +
                    host_data["enhancement"] * factor_enh
                )
            output.append(host_data)
    return output


def advanced_currency(search):
    """
    Advanced form of the system currency report.

    Return a list of dictts.
    """

    output = []

    # Get all hosts (for more than 10000 hosts, this will take a long time)
    hosts = get_with_json(
        "{}hosts{}".format(api, search),
        json.dumps({"per_page": "10000"})
    )["results"]

    # Multiply factors according to "spacewalk-report system-currency"
    factor_cri = 32
    factor_imp = 16
    factor_mod = 8
    factor_low = 4
    factor_bug = 2
    factor_enh = 1

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
            if(
                    "total" in erratas and
                    "content_facet_attributes" in host and
                    "subscription_facet_attributes" in host
            ):

                host_data["content_view"] = host[
                    "content_facet_attributes"]["content_view"]["name"]
                content_view_id = host[
                    "content_facet_attributes"]["content_view"]["id"]
                host_data["lifecycle_environment"] = host[
                    "content_facet_attributes"][
                        "lifecycle_environment"]["name"]
                lifecycle_environment_id = host[
                    "content_facet_attributes"]["lifecycle_environment"]["id"]
                host_data["subscription_os_release"] = host[
                    "subscription_facet_attributes"]["release_version"]
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
            host_data["score"] = (
                factor_cri * host_data["critical"] +
                factor_imp * host_data["important"] +
                factor_mod * host_data["moderate"] +
                factor_low * host_data["low"] +
                factor_bug * host_data["bug"] +
                factor_enh * host_data["enhancement"]
            )
            output.append(host_data)
    return output


def library_currency():
    """Advanced form of the system currency report, with more errata detail."""

    if args.organization is None:
        print("Organization must be specified for Library report")
        sys.exit(1)

    # Print headline
    print(
        ','.join(str(x) for x in [
            "system_id",
            "org_name",
            "name",
            "total_available_security",
            "critical",
            "important",
            "moderate",
            "low",
            "bug",
            "enhancement",
            "score",
            "total_applicable_security",
            "applicable_critical",
            "applicable_important",
            "applicable_moderate",
            "applicable_low",
            "applicable_bug",
            "applicable_enhancement",
            "applicable_score",
            "content_view",
            "content_view_publish_date",
            "lifecycle_environment",
            "subscription_os_release",
            "os_release",
            "arch",
            "subscription_status",
            "comment",
        ]
                 )
    )

    # Open reports files
    available_file = open('available_errata.csv', 'w')
    available_file.write(
        "system_id,org_name,name,state,errata_id,issued,"
        "updated,severity,type,reboot_suggested,title,further_info\n"
    )
    applicable_file = open('applicable_errata.csv', 'w')
    applicable_file.write(
        "system_id,org_name,name,state,errata_id,issued,"
        "updated,severity,type,reboot_suggested,title,further_info\n"
    )

    # Red Hat errata URL
    RH_URL = "https://access.redhat.com/errata/"

    # Find organization
    organization = get_with_json(
        "{}/organizations/?Search={}".format(katello_api, args.organization),
        json.dumps({"per_page": "10000"})
    )["results"]
    organization_id = organization[0]["id"]
    # print str(organization_id)

    # Find lifecycle_environment
    lifecycle_environment_compare = get_with_json(
        "{}/organizations/{}/environments?name={}".format(
            katello_api, str(organization_id), args.environment),
        json.dumps({"per_page": "10000"})
    )["results"]
    lifecycle_environment_compare_id = lifecycle_environment_compare[0]["id"]
    # print str(lifecycle_environment_compare_id)

    # Find content view
    content_view_compare = get_with_json(
        "{}/organizations/{}/content_views?name={}".format(
            katello_api, str(organization_id), args.contentview),
        json.dumps({"per_page": "10000"})
    )["results"]
    content_view_compare_id = content_view_compare[0]["id"]
    # print str(content_view_compare_id)

    # Get all hosts (for more than 10000 hosts, this will take a long time)
    hosts = get_with_json(
        "{}hosts{}".format(api, args.search),
        json.dumps({"per_page": "10000"})
    )["results"]

    # Multiply factors according to "spacewalk-report system-currency"
    factor_cri = 32
    factor_imp = 16
    factor_mod = 8
    factor_low = 4
    factor_bug = 2
    factor_enh = 1

    for host in hosts:

        # Get all errata for each host
        erratas = get_with_json(
            "{}hosts/{}/errata".format(api, str(host["id"])),
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

            errata_count_sec = 0
            errata_count_cri = 0
            errata_count_imp = 0
            errata_count_mod = 0
            errata_count_low = 0
            errata_count_enh = 0
            errata_count_bug = 0

            applicable_errata_count_sec = 0
            applicable_errata_count_cri = 0
            applicable_errata_count_imp = 0
            applicable_errata_count_mod = 0
            applicable_errata_count_low = 0
            applicable_errata_count_enh = 0
            applicable_errata_count_bug = 0

            # Check if host have any errrata at all
            if (
                    "total" in erratas and
                    "content_facet_attributes" in host and
                    "subscription_facet_attributes" in host
            ):
                content_view_name = host[
                    "content_facet_attributes"]["content_view"]["name"]
                content_view_id = host[
                    "content_facet_attributes"]["content_view"]["id"]
                lifecycle_environment = host[
                    "content_facet_attributes"][
                        "lifecycle_environment"]["name"]
                lifecycle_environment_id = host[
                    "content_facet_attributes"]["lifecycle_environment"]["id"]
                subscription_os_release = host[
                    "subscription_facet_attributes"]["release_version"]
                arch = host["architecture_name"]
                subscription_status = host["subscription_status_label"]
                os_release = host["operatingsystem_name"]

                content_view = get_with_json(
                    "{}/content_views/{}/content_view_versions?"
                    "environment_id={}".format(
                        katello_api,
                        str(content_view_id),
                        str(lifecycle_environment_id)
                    ),
                    json.dumps({"per_page": "10000"})
                )["results"]

                cv_date = content_view[0]["created_at"]

                # Go through each errata that is available
                for errata in erratas["results"]:

                    # If it is a security errata, check the severity
                    if errata["type"] == "security":
                        errata_count_sec += 1
                        if errata["severity"] == "Critical":
                            errata_count_cri += 1
                        if errata["severity"] == "Important":
                            errata_count_imp += 1
                        if errata["severity"] == "Moderate":
                            errata_count_mod += 1
                        if errata["severity"] == "Low":
                            errata_count_low += 1

                    if errata["type"] == "enhancement":
                        errata_count_enh += 1
                    if errata["type"] == "bugfix":
                        errata_count_bug += 1

                    # Delete any commas from the errata title
                    # eg: https://access.redhat.com/errata/RHSA-2017:0817
                    errata["title"] = errata["title"].replace(',', '')
                    available_file.write(
                        ','.join(str(x) for x in [
                            str(host["id"]),
                            str(host["organization_name"]),
                            host["name"],
                            "Available",
                            str(errata["errata_id"]),
                            str(errata["issued"]),
                            str(errata["updated"]),
                            str(errata["severity"]),
                            str(errata["type"]),
                            str(errata["reboot_suggested"]),
                            str(errata["title"]),
                            "{}{}\n".format(RH_URL, str(errata["errata_id"])),
                        ]
                                 )
                    )

                # Go through each errata that is applicable (in the library)
                for errata in applicable_erratas["results"]:

                    # If it is a security errata, check the severity
                    if errata["type"] == "security":
                        applicable_errata_count_sec += 1
                        if errata["severity"] == "Critical":
                            applicable_errata_count_cri += 1
                        if errata["severity"] == "Important":
                            applicable_errata_count_imp += 1
                        if errata["severity"] == "Moderate":
                            applicable_errata_count_mod += 1
                        if errata["severity"] == "Low":
                            applicable_errata_count_low += 1

                    if errata["type"] == "enhancement":
                        applicable_errata_count_enh += 1
                    if errata["type"] == "bugfix":
                        applicable_errata_count_bug += 1

                    # Delete any commas from the errata title
                    # eg: https://access.redhat.com/errata/RHSA-2017:0817
                    errata["title"] = errata["title"].replace(',', '')
                    applicable_file.write(
                        ','.join(str(x) for x in [
                            str(host["id"]),
                            str(host["organization_name"]),
                            host["name"],
                            "Applicable",
                            str(errata["errata_id"]),
                            str(errata["issued"]),
                            str(errata["updated"]),
                            str(errata["severity"]),
                            str(errata["type"]),
                            str(errata["reboot_suggested"]),
                            str(errata["title"]),
                            "{}{}\n".format(RH_URL, str(errata["errata_id"])),
                        ]
                                 )
                    )

            # Calculate weighted score
            score = (
                factor_cri * errata_count_cri +
                factor_imp * errata_count_imp +
                factor_mod * errata_count_mod +
                factor_low * errata_count_low +
                factor_bug * errata_count_bug +
                factor_enh * errata_count_enh
            )
            applicable_score = (
                factor_cri * applicable_errata_count_cri +
                factor_imp * applicable_errata_count_imp +
                factor_mod * applicable_errata_count_mod +
                factor_low * applicable_errata_count_low +
                factor_bug * applicable_errata_count_bug +
                factor_enh * applicable_errata_count_enh
            )

            # Print result
            print(
                ','.join(str(x) for x in [
                    str(host["id"]),
                    str(host["organization_name"]),
                    host["name"],
                    str(errata_count_sec),
                    str(errata_count_cri),
                    str(errata_count_imp),
                    str(errata_count_mod),
                    str(errata_count_low),
                    str(errata_count_bug),
                    str(errata_count_enh),
                    str(score),
                    str(applicable_errata_count_sec),
                    str(applicable_errata_count_cri),
                    str(applicable_errata_count_imp),
                    str(applicable_errata_count_mod),
                    str(applicable_errata_count_low),
                    str(applicable_errata_count_bug),
                    str(applicable_errata_count_enh),
                    str(applicable_score),
                    str(content_view_name),
                    str(cv_date),
                    str(lifecycle_environment),
                    str(subscription_os_release),
                    str(os_release),
                    str(arch),
                    str(subscription_status),
                    str(host["comment"]),
                ]
                         )
            )

    available_file.closed
    applicable_file.closed


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
        choices=["csv", "json", "yaml"],
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

    init(server)

    search_dict = search_queries(args.search)
    if args.organization:
        search_dict['organization'] = args.organization
    search_string = search_string(search_dict)

    if args.advanced:
        output = advanced_currency(search_string)
    elif args.library:
        output = library_currency(search_string)
    else:
        output = simple_currency(search_string)

    if args.output == 'csv':
        output_csv(output)
    elif args.output == 'json':
        print(output_json(output))
    elif args.output == 'yaml':
        print(output_yaml(output))
