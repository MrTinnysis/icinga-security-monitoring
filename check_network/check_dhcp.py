#!/usr/bin/env python3

import argparse
import os
import sys
import re

#
# Inspired by:
# https://scapy.readthedocs.io/en/latest/usage.html#identifying-rogue-dhcp-servers-on-your-lan
#

from scapy.all import srp, Ether, IP, UDP, BOOTP, DHCP, conf, get_if_raw_hwaddr

# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

arg_format_regex = re.compile(
    r"((?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})(?:,|, )((?:\d{1,3}\.){3}\d{1,3})")


def mac_ip_tuple(arg):
    # check arg format
    match = arg_format_regex.match(arg)

    if not match:
        raise argparse.ArgumentTypeError("Invalid format")

    mac = match.group(1)
    ip = match.group(2)

    return (mac, ip)


def parse_args():
    # Parses the CLI Arguments and returns a dict containing the
    # corresponding values
    argumentParser = argparse.ArgumentParser()

    argumentParser.add_argument(
        '-v', '--verbose', nargs="?", const=True, default=False,
        help='verbose output'
    )
    argumentParser.add_argument(
        "-wl", "--white-list", nargs="+", type=mac_ip_tuple, required=True,
        help="Specify DHCP Server whitelist \"mac, ip\" pairs"
    )
    argumentParser.add_argument(
        "-t", "--timeout", type=int, default=5,
        help="Specify the amount of seconds that should be waited for DHCP Responses"
    )

    return argumentParser.parse_args()


def get_dhcp_discovery(verbose=False):
    # get interface hw addr
    _, hw = get_if_raw_hwaddr(conf.iface)

    if verbose:
        print(f"Interface: {conf.iface} -> {hw}")

    dhcp_discovery = Ether(dst="ff:ff:ff:ff:ff:ff")/IP(
        src="0.0.0.0", dst="255.255.255.255")/UDP(
            sport=68, dport=67)/BOOTP(chaddr=hw)/DHCP(
                options=[("message-type", "discover"), "end"])

    if verbose:
        print(f"DHCP Discovery: {dhcp_discovery.show()}")

    return dhcp_discovery


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    conf.checkIPaddr = False

    # build dhcp discovery packet
    dhcp_discovery = get_dhcp_discovery(args.verbose)

    # send packet and wait {timeout} seconds for responses
    answer_pkts, unanswered_pkts = srp(
        dhcp_discovery, multi=True, timeout=args.timeout)

    if args.verbose:
        answer_pkts.summary()

    # check if there was at least one answer
    if len(unanswered_pkts) > 0:
        print(
            f"WARNING: DHCP Discovery remained unanswered for {args.timeout} sec.")
        sys.exit(WARNING)

    # get (mac, ip) pairs for each response
    dhcp_servers = [(pkt[1][Ether].src, pkt[1][IP].src) for pkt in answer_pkts]

    # remove all whitelisted dhcp servers from list
    dhcp_servers = [
        dhcp for dhcp in dhcp_servers if not dhcp in args.white_list]

    # check if there remain any unkown dhcp servers
    if len(dhcp_servers) > 0:
        print(
            f"CRITICAL: Unknown DHCP Server(s) detected: {dhcp_servers}")
        sys.exit(CRITICAL)

    print("OK: No unknown DHCP Servers detected.")
    sys.exit(OK)


if __name__ == "__main__":
    main()
