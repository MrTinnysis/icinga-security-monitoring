#!/usr/bin/env python3

import argparse
import os
import sys
import re
import requests

from ipaddress import ip_network, ip_address
from datetime import date, timedelta
from JournalReader import JournalReader

# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


class DropList:
    def __init__(self, file):
        self.file = file
        if not os.path.isfile(self.file):
            self.drop_list = self._retrieve_drop_list()
        else:
            with open(self.file, "r") as f:
                timestamp = date.fromisoformat(f.readline()[2:-1])

            # check timestamp
            if date.today() - timestamp >= timedelta(days=1):
                self.drop_list = self._retrieve_drop_list()
            else:
                self.drop_list = self._parse_drop_list()

    def contains_ip(self, ip):
        ip = ip_address(ip)
        return any(ip in network for network in self.drop_list)

    def _retrieve_drop_list(self):
        # retrieve DROP and EDROP list
        drop = requests.get("https://www.spamhaus.org/drop/drop.txt").text
        edrop = requests.get("https://www.spamhaus.org/drop/edrop.txt").text

        # write both lists into the file
        with open(self.file, "w") as file:
            file.write("; " + date.today().isoformat() + "\n")
            file.write(drop)
            file.write(edrop)

        return self._parse_drop_list()

    def _parse_drop_list(self):
        with open(self.file, "r") as file:
            return [ip_network(line.split(" ; ")[0]) for line in file if not line.startswith(";")]


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
    # argumentParser.add_argument(
    #     "-o", "--outbound", default=None,
    #     help="Specify the log prefix used for outbound connections"
    # )
    # argumentParser.add_argument(
    #     "-i", "--inbound", default=None,
    #     help="Specify the log prefix used for inbound connections"
    # )
    argumentParser.add_argument(
        "-d", "--drop-list", default="/tmp/drop_list.txt",
        help="Specify the location where the droplist should be cached"
    )

    return argumentParser.parse_args()


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # Get drop_list
    drop_list = DropList(args.drop_list)

    # setup journal reader
    journal = JournalReader(args.journal_path)

    # setup journal
    journal.add_match("SYSLOG_IDENTIFIER=kernel")
    journal.set_timeframe(args.period)

    # compile regex used to match IPs
    ip_regex = re.compile(
        r"SRC=((?:\d{1,3}\.){3}\d{1,3}) DST=((?:\d{1,3}\.){3}\d{1,3})")

    ip_set = set()

    for entry in journal:
        # get log message
        msg = entry["MESSAGE"]
        # get src and dst ip from msg
        match = ip_regex.search(msg)

        if match:
            # add both src and dst ip to ip_set
            ip_set.add(match.group(1))
            ip_set.add(match.group(2))

    if args.verbose:
        print(f"Num IPs: {len(ip_set)}")

    # filter ips by droplist (set comprehension)
    ip_set = {ip for ip in ip_set if drop_list.contains_ip(ip)}

    if args.verbose:
        print(f"Num IPs after filtering: {len(ip_set)}")

    returnCode = OK

    if len(ip_set) > 0:
        print(f"CRITICAL: Malicious IPv4 traffic detected: {ip_set}")
        returnCode = CRITICAL

    # # retrieve entries from journal
    # inbound = set()
    # outbound = set()

    # for entry in journal:
    #     msg = entry["MESSAGE"]

    #     if msg.startswith(args.inbound):
    #         # inbound traffic
    #         match = ip_regex.search(msg)

    #         if match:
    #             # track inbound traffic's src IP
    #             inbound.add(match.group(1))

    #     elif msg.startswith(args.outbound):
    #         # outbound traffic
    #         match = ip_regex.search(msg)

    #         if match:
    #             # track outbound traffic's dst IP
    #             outbound.add(match.group(2))

    # if args.verbose:
    #     print(f"Inbound Connections: {len(inbound)}")
    #     print(f"Outbound Connections: {len(outbound)}")

    # # filter ips by drop_list
    # inbound = [ip for ip in inbound if drop_list.contains_ip(ip)]
    # outbound = [ip for ip in outbound if drop_list.contains_ip(ip)]

    # if args.verbose:
    #     print(f"Inbound Malicious: {len(inbound)}")
    #     print(f"Outbound Malicious: {len(outbound)}")

    # returnCode = OK

    # if len(inbound) > 0:
    #     returnCode = CRITICAL
    #     print(
    #         f"CRITICAL: Inbound connections from malicious IPs detected: {inbound}")

    # if len(outbound) > 0:
    #     returnCode = CRITICAL
    #     print(
    #         f"CRITICAL: Outbound connections to malicious IPs detected: {outbound}")

    if returnCode == OK:
        print("OK: No malicious IPv4 traffic detected.")

    sys.exit(returnCode)


if __name__ == "__main__":
    main()
