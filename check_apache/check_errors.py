#!/usr/bin/env python3

import argparse
import sys
import os
import re

from ApacheLogs import ApacheLogParser
from datetime import datetime, timedelta
from itertools import groupby


# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

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
        "-p", "--path", default="/etc/apache2/apache2.conf",
        help="specify the config file that should be loaded (used to locate corresponding log files)"
    )
    argumentParser.add_argument(
        "-e", "--env", nargs="?", const="/etc/apache2/envvars", default=None,
        help="specify the environment variables file to load (used to parse the config file)"
    )
    argumentParser.add_argument(
        "-vh", "--vhost", default=None,
        help="specify the virtual host whose config should be loaded (if any)"
    )
    argumentParser.add_argument(
        '--period', metavar='NUMBER', default='1h', type=period,
        help='check log of last period (default: "1h", format 1-99 m/h/d)'
    )
    argumentParser.add_argument(
        '-w', '--warning', metavar='NUMBER', type=int, default=1,
        help='return warning if number of found log entries is above'
    )
    argumentParser.add_argument(
        '-c', '--critical', metavar='NUMBER', type=int, default=2,
        help='return critical if number of found logs is above'
    )
    argumentParser.add_argument(
        "-rc", "--return-codes", nargs="+", default=["403", "404"],
        help="specify which return codes should be monitored"
    )

    return argumentParser.parse_args()


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # check file paths
    if not os.path.isfile(args.path):
        print(f"CRITICAL: {args.path} does not denote a file!")
        sys.exit(CRITICAL)

    if args.env and not os.path.isfile(args.env):
        print(f"CRITICAL: {args.env} does not denote a file!")
        sys.exit(CRITICAL)

    # get start datetime from configured period
    start_datetime = _get_start_datetime(args.period)

    if args.verbose:
        print(f"start_datetime_iso={start_datetime}")

    parser = ApacheLogParser.from_path(args.path, args.env, args.vhost)

    log_data = parser.get_log_data(lambda x: datetime.fromisoformat(
        x["time_received_isoformat"]) >= start_datetime and x["status"] in args.return_codes)

    total_count = len(log_data)

    if args.verbose:
        print(f"total_count={total_count}")

    returnCode = OK

    # count entries per ip
    rhost_list = groupby(sorted(
        log_data, key=lambda x: x["remote_host"]), key=lambda x: x["remote_host"])

    returnCode = OK

    for rhost in rhost_list:
        (ip, entries) = rhost
        size = sum(1 for _ in entries)
        print(f"|{ip}={size};{args.warning};{args.critical}")

        if size >= args.warning:
            returnCode = max(returnCode, WARNING)

        if size >= args.critical:
            returnCode = max(returnCode, CRITICAL)

    sys.exit(returnCode)


class InvalidTimeframeException(Exception):
    pass


def _get_start_datetime(period):
    # get current date
    now = datetime.now()
    # match period -> extract quantity and type
    match = re.match('(\d{1,2})([dhm])', period)

    if not match:
        raise InvalidTimeframeException()

    # set quantity for given type and all others to 0
    quantity = {"d": 0, "h": 0, "m": 0}
    quantity[match.group(2)] = max(int(match.group(1)), 1)

    # calculate start date
    now -= timedelta(days=quantity["d"],
                     hours=quantity["h"], minutes=quantity["m"])

    return now


if __name__ == "__main__":
    main()
