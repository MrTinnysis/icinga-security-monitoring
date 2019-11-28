#!/usr/bin/env python3

import argparse
import os
import sys
import re
import requests

from datetime import date, timedelta
from JournalReader import JournalReader

# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


class DropList:
    def __init__(self, file="/tmp/drop_list.txt"):
        self.file = file
        if not os.path.isfile(self.file):
            self.data = self._retrieve_drop_list()
        else:
            with open(self.file, "r") as f:
                timestamp = date.fromisoformat(f.readline()[2:])

            # check timestamp
            if date.today() - timestamp > timedelta(days=1):
                self.data = self._retrieve_drop_list()
            else:
                self.data = self._parse_drop_list()

    def contains_ip(self, ip):
        for line in self.data:
            network, netmask = line.split("/")
        pass

    def _retrieve_drop_list(self):
        # retrieve DROP and EDROP list
        drop = requests.get("https://www.spamhaus.org/drop/drop.txt").text
        edrop = requests.get("https://www.spamhaus.org/drop/edrop.txt").text

        # write both lists into the file
        with open(self.file, "w+") as file:
            file.write("; " + date.today().isoformat())
            file.write(drop)
            file.write(edrop)

        return self._parse_drop_list()

    def _parse_drop_list(self):
        with open(self.file, "r") as file:
            return [line.split(" ; ")[0] for line in file if not line.startsWith(";")]

    def __repr__(self):
        return self.data.__repr__()



# define period
def period(string):
    if not re.search("^\d{1,2}[dhm]$", string):
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
        "-jp", '--journal-path',
        help='path to journal log folder'
    )
    argumentParser.add_argument(
        "-p", '--period', metavar='NUMBER', default='1h', type=period,
        help='check log of last period (default: "1h", format 1-99m/h/d)'
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
    # check if DROP and EDROP list are present and up-to-date
    # if not: reload DROP and EDROP list (once per day)
    #drop_list = get_drop_list()
    drop_list = DropList()

    if args.verbose:
        print(drop_list)

    sys.exit(OK)

    # setup journal reader
    journal = JournalReader(args.journal_path)

    # setup journal
    journal.add_match("SYSLOG_IDENTIFIER=kernel")
    journal.set_timeframe(args.period)

    # compile regex used to match IPs
    ip_regex = re.compile(
        r"SRC=((?:\d{1,3}\.){3}\d{1,3}) DST=((?:\d{1,3}\.){3}\d{1,3})")

    # retrieve entries from journal
    inbound = outbound = []

    for entry in journal:
        match = ip_regex.search(entry["MESSAGE"])

        # check if IPs were matched and if dest ip differs from broadcast
        if match and match.group(2) != "255.255.255.255":
            inbound += [match.group(1)]
            outbound += [match.group(2)]

    # filter ips by drop_list
    inbound = [ip for ip in inbound if drop_list.contains_ip(ip)]
    outbound = [ip for ip in outbound if drop_list.contains_ip(ip)]

    returnCode = OK

    if len(inbound) > 0:
        returnCode = CRITICAL
        print(
            f"CRITICAL: Inbound connections from malicious IPs detected: {inbound}")

    if len(outbound) > 0:
        returnCode = CRITICAL
        print(
            f"CRITICAL: Outbound connections to malicious IPs detected: {outbound}")

    if returnCode == OK:
        print("OK: No malicious connections detected.")

    sys.exit(returnCode)


if __name__ == "__main__":
    main()

