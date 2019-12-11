#!/usr/bin/env python3

import argparse
import sys
import re
import socket

# pylint: disable=import-error
from JournalReader import JournalReader

# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


# define period
def period(string):
    if not re.search(r"^\d{1,2}[dhm]$", string):
        msg = "%r is not a valid period" % string
        raise argparse.ArgumentTypeError(msg)
    return string


def parse_args():
    # Parses the CLI Arguments and returns a dict containing the
    # corresponding values
    argumentParser = argparse.ArgumentParser()

    argumentParser.add_argument(
        '-v', '--verbose', nargs="?", const=True, default=False,
        help='verbose output'
    )
    argumentParser.add_argument(
        "-j", '--journal-path',
        help='path to journal log folder'
    )
    argumentParser.add_argument(
        "-p", '--period', metavar='NUMBER', default='30m', type=period,
        help='check log of last period (default: "30m", format 1-99m/h/d)'
    )
    argumentParser.add_argument(
        "-t", "--threshold", default=30, type=int,
        help=""
    )

    return argumentParser.parse_args()


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # setup journal reader
    journal = JournalReader(args.journal_path)

    # setup journal
    journal.add_match("SYSLOG_IDENTIFIER=kernel")
    journal.set_timeframe(args.period)

    # get the current machines IP address
    local_ip = socket.gethostbyname(socket.gethostname())

    # compile regex used to match IPs
    ip_regex = re.compile(
        r"SRC=((?:\d{1,3}\.){3}\d{1,3}) DST=((?:\d{1,3}\.){3}\d{1,3})")
    # compile regex used to match ports
    port_regex = re.compile(
        r"SPT=(\d+) DPT=(\d+)")

    # dict used to match src ip to dst ports
    ip_dict = {}

    # process journal entries
    for entry in journal:
        # get log message
        msg = entry["MESSAGE"]

        # match ips and ports
        ip_match = ip_regex.search(msg)
        port_match = port_regex.search(msg)

        if ip_match and port_match:
            # get src ip and dst port
            src_ip = ip_match.group(1)
            dst_port = port_match.group(2)

            # skip outbound ip packets
            if src_ip == local_ip:
                continue

            # initialize empty port set for src ip if not already exists
            port_set = ip_dict.setdefault(src_ip, set())

            # add dst port to port set
            port_set.add(dst_port)

    if args.verbose:
        print(f"Max Ports connected: {max((len(ports) for ports in ip_dict.values()), default=0)}")

    returnCode = OK

    # process each ip
    for ip, ports in ip_dict.items():
        # compare number of dst ports with threshold
        if len(ports) > args.threshold:
            print(f"CRITICAL: Portscan detected: {ip}")
            returnCode = CRITICAL

    if returnCode == OK:
        print(f"OK: No Portscans detected")

    sys.exit(returnCode)

if __name__ == "__main__":
    main()
