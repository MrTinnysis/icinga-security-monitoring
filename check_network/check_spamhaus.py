#!/usr/bin/env python3

import argparse
import os
import sys
import re
import dns.resolver


# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


def parse_args():
    # Parses the CLI Arguments and returns a dict containing the
    # corresponding values
    argumentParser = argparse.ArgumentParser()

    argumentParser.add_argument(
        '-v', '--verbose', nargs="?", const=True, default=False,
        help='verbose output'
    )
    argumentParser.add_argument(
        "-d", "--domain", required=True,
        help="Specify the domain that should be checked against the spamhaus block lists"
    )

    return argumentParser.parse_args()


def ns_lookup(domain):
    ips = []
    try:
        ipv4 = dns.resolver.query(domain, "A", raise_on_no_answer=False)
        ipv6 = dns.resolver.query(domain, "AAAA", raise_on_no_answer=False)
    except:
        print(f"UNKNOWN: Could not resolve domain name: {domain}")
        sys.exit(UNKNOWN)

    ips += ipv4
    ips += ipv6
    return ips


def is_domain_listed(domain):
    pass


def is_ip_listed(ip):
    pass


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # get ip address for given domain
    ip_list = ns_lookup(args.domain)

    print(ip_list)

    sys.exit(OK)

    returnCode = OK

    # check domain against spamhaus domain block list
    if is_domain_listed(args.domain):
        print(f"CRITICAL: ...")
        returnCode = CRITICAL

    # check ip against spamhaus zen block list
    if any(is_ip_listed(ip) for ip in ip_list):
        print(f"CRITICAL: ...")
        returnCode = CRITICAL

    if returnCode == OK:
        print(f"OK: ...")

    sys.exit(returnCode)


if __name__ == "__main__":
    main()
