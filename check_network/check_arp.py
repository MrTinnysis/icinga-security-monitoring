#!/usr/bin/env python3

import argparse
import os
import sys
import re

from scapy.all import srp, conf, get_if_hwaddr, Ether, ARP, Route

# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

ip_addr_format = re.compile(r"((?:\d{1,3}\.){3}\d{1,3})")


def ip_addr(arg):
    match = ip_addr_format.match(arg)

    if not match:
        raise argparse.ArgumentTypeError("Invalid format")

    return match.group(1)


def get_default_gateway(ip=None):
    # retrieve the default gateway for the given ip from routing table
    _, _, gateway = Route().route(ip)
    return gateway


def parse_args():
    # Parses the CLI Arguments and returns a dict containing the
    # corresponding values
    argumentParser = argparse.ArgumentParser()

    argumentParser.add_argument(
        '-v', '--verbose', nargs="?", const=True, default=False,
        help='verbose output'
    )
    argumentParser.add_argument(
        "-ip", type=ip_addr, default=get_default_gateway(),
        help="Specify the ip address that should be used to detect arp spoofing"
    )
    argumentParser.add_argument(
        "-if", "--interface", default=conf.iface,
        help="Specify the interface that should be used to detect arp spoofing"
    )
    argumentParser.add_argument(
        "-t", "--timeout", type=int, default=5,
        help="Specify the amount of seconds that should be waited for ARP Responses"
    )

    return argumentParser.parse_args()


def get_arp_request(ip, mac):
    return Ether(dst="ff:ff:ff:ff:ff:ff", src=mac)/ARP(hwlen=6, plen=4, hwsrc=mac, pdst=ip)


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # retrieve current ip and default gateway from routing table
    # _, ip, gateway = Route().route()

    # if args.verbose:
    #     print(f"Local IP={ip}")
    #     print(f"Gateway={gateway}")

    # # if no ip is specified, use default gateway
    # if not args.ip:
    #     args.ip = gateway

    # ensure specified ip is not the current ip
    # if ip == args.ip:
    #     raise AssertionError("Cannot send ARP request for local IP address!")

    # get mac address for specified interface
    mac = get_if_hwaddr(args.interface)

    if args.verbose:
        print(f"Interface: {args.interface}")
        print(f"MAC: {mac}")
        print(f"IP: {args.ip}")

    # build arp request for ip
    arp = get_arp_request(args.ip, mac)

    if args.verbose:
        arp.show()

    try:
        # send arp request and wait {timeout} seconds for responses
        answer_pkts, unanswered_pkts = srp(
            arp, multi=True, timeout=args.timeout, filter="arp", verbose=(2 if args.verbose else 0))
    except PermissionError as err:
        print(
            f"UNKNOWN: Insufficient permissions to send network packet: {err}")
        sys.exit(UNKNOWN)

    if args.verbose:
        answer_pkts.summary()

    # check if a response was received
    if len(unanswered_pkts) > 0:
        print(
            f"UNKNOWN: ARP Request remained unanswered for {args.timeout} seconds, not a valid IP address?")
        sys.exit(UNKNOWN)

    # check if more than one responses were received
    if len(answer_pkts) > 1:
        print(f"CRITICAL: Multiple ARP Responses received!")
        sys.exit(CRITICAL)

    print(f"OK: Nothing unusual.")
    sys.exit(OK)


if __name__ == "__main__":
    main()
