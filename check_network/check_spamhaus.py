#!/usr/bin/env python3

import argparse
import os
import sys
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
    try:
        ipv4 = dns.resolver.query(domain, "A")
    except Exception as ex:
        print(f"UNKNOWN: Could not resolve domain name: {domain} due to: {ex}")
        sys.exit(UNKNOWN)

    # convert ips to text representation
    ipv4 = [ip.to_text() for ip in ipv4]

    return ipv4

    ##
    # IPv6 currently no supported¨!
    ##

    # ips = []
    # try:
    #     # retrieve ipv4 and ipv6 addresses of given domain
    #     ipv4 = dns.resolver.query(domain, "A", raise_on_no_answer=False)
    #     ipv6 = dns.resolver.query(domain, "AAAA", raise_on_no_answer=False)
    # except:
    #     print(f"UNKNOWN: Could not resolve domain name: {domain}")
    #     sys.exit(UNKNOWN)

    # # collect ips
    # ips += [ip.to_text() for ip in ipv4]
    # ips += [ip.to_text() for ip in ipv6]

    # if len(ips) == 0:
    #     print(f"UNKNOWN: Could not resolve domain name: {domain}")
    #     sys.exit(UNKNOWN)

    # return ips


def is_domain_listed(domain):
    query = f"{domain}.dbl.spamhaus.org"

    try:
        dns.resolver.query(query, "A")
    except dns.resolver.NXDOMAIN:
        # we expect an NXDOMAIN if the domain is not listed on the DBL
        return False
    except Exception as ex:
        # abort execution on all other exceptions
        print(f"UNKNOWN: Could not check spamhaus DBL due to: {ex}")
        sys.exit(UNKNOWN)
    else:
        # if no NXDOMAIN exception was thrown, the domain is listed
        return True


def get_domain_listing_reason(domain):
    query = f"{domain}.dbl.spamhaus.org"

    try:
        answers = dns.resolver.query(query, "TXT")
    except:
        # if this fails we just can't display the reason
        # no need to abort here...
        return ""
    else:
        return answers[0].to_text()


def is_ip_listed(ip):
    # reverse ip for blocklist query: 192.168.1.1 -> 1.1.168.192
    reversed_ip = ".".join(ip.split(".")[::-1])
    query = f"{reversed_ip}.zen.spamhaus.org"

    try:
        dns.resolver.query(query, "A")
    except dns.resolver.NXDOMAIN:
        # we expect an NXDOMAIN if the IP is not listed on the block list
        return False
    except Exception as ex:
        # abort executtion on all other exceptions
        print(f"UNKNOWN: Could not check spamaus zen block list due to: {ex}")
        sys.exit(UNKNOWN)
    else:
        # if no NXDOMAIN exception was thrown, the ip is listed
        return True


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # get ip address for given domain
    ip_list = ns_lookup(args.domain)

    if args.verbose:
        print(f"Domain: {args.domain}")
        print(f"IPs: {ip_list}")

    returnCode = OK

    # check domain against spamhaus domain block list
    if is_domain_listed(args.domain):
        reason = get_domain_listing_reason(args.domain)
        print(f"CRITICAL: The domain is listed on the DBL: {reason}")
        returnCode = CRITICAL

    # check if any ip associated with the given domain is on a block list
    if any(is_ip_listed(ip) for ip in ip_list):
        print(
            f"CRITICAL: At least one of the IPv4 addresses associated with '{args.domain}' is on the zen block list")
        returnCode = CRITICAL

    if returnCode == OK:
        print(f"OK: Neither the domain nor associated IPv4 addresses are listed.")

    sys.exit(returnCode)


if __name__ == "__main__":
    main()
