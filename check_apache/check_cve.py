#!/usr/bin/env python3

import argparse
import sys
import subprocess
import re
import requests
from xml.etree import ElementTree


# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

# integers indicating cve severity levels:
CVE_SEVERITIES = {
    "critical": 4,
    "important": 3,
    "moderate": 2,
    "low": 1,
    "n/a": 0
}


def parse_args():
    # Parses the CLI Arguments and returns a dict containing the
    # corresponding values
    argumentParser = argparse.ArgumentParser()

    argumentParser.add_argument(
        '-v', '--verbose', nargs="?", const=True, default=False,
        help='verbose output')
    argumentParser.add_argument(
        "-w", '--warning', type=int, choices=CVE_SEVERITIES.values(), default=3,
        help='return warning if cve severity is equal or above')
    argumentParser.add_argument(
        "-c", '--critical', type=int, choices=CVE_SEVERITIES.values(), default=4,
        help='return critical if cve severity is equal or above')
    argumentParser.add_argument(
        "-e", "--exec", default="httpd", choices=["httpd", "apache2"],
        help="Specify the executable that should be used to query the server version"
    )

    return argumentParser.parse_args()


def get_server_version(exec_name, verbose):
    cmd = exec_name + " -v | grep 'Server version:'"

    try:
        # execute shell commands to retrieve server version
        server_version = subprocess.check_output(
            cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"CRITICAL: Failed to execute shell command: {cmd}")
        sys.exit(CRITICAL)

    if verbose:
        print(server_version)

    # retrieve server version number using regex
    match = re.match("^Server version: Apache/(.+?) ", server_version)

    # check if match was successful
    if not match:
        print("CRITICAL: Could not retrieve server version")
        sys.exit(CRITICAL)

    if verbose:
        print(f"version_nr: {match.group(1)}")

    return match.group(1)


def get_cve_list(verbose):
    try:
        # retrieve CVE's in xml form
        response = requests.get(
            "https://httpd.apache.org/security/vulnerabilities-httpd.xml", timeout=5)
    except TimeoutError:
        print("CRITICAL: Could not retrieve CVE's (request timed out)")
        sys.exit(CRITICAL)

    if verbose:
        print(f"response_header={response.headers}")

    # check if http response was successful
    if response.status_code != 200:
        print("CRITICAL: Could not retrieve CVE's")
        sys.exit(CRITICAL)

    # parse response xml and retrieve all cve's (issues)
    return ElementTree.fromstring(response.text).findall(".//issue")


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # get server version and cve's (in xml format)
    server_version = get_server_version(args.exec, args.verbose)
    cve_list = get_cve_list(args.verbose)

    # filter cve's by affected server version and map them onto their
    # severity number as defined in CVE_SEVERITIES
    severity_list = [CVE_SEVERITIES[cve.find(".//severity").text] for cve in cve_list if
                     cve.find(f".//affects[@version='{server_version}']") != None]

    if args.verbose:
        print(f"severity_list={severity_list}")

    # get highest severity cve affecting the given server version
    max_severity = max(severity_list, default=CVE_SEVERITIES["n/a"])

    if args.verbose:
        print(f"max_severity={max_severity}")

    # check critical threshold
    if max_severity >= args.critical:
        print(f"CRITICAL: severity={max_severity}")
        sys.exit(CRITICAL)

    # check warning threshold
    if max_severity >= args.warning:
        print(f"WARNING: severity={max_severity}")
        sys.exit(WARNING)

    print(f"OK: severity={max_severity}")
    sys.exit(OK)


if __name__ == "__main__":
    main()
