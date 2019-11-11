#!/usr/bin/env python3

import argparse
import os
import json
import sys

from datetime import date, timedelta
from FileSystemCheck import FSCheck


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
        help='verbose output')
    argumentParser.add_argument(
        "-p", "--path", default="/tmp",
        help=""
    )
    argumentParser.add_argument(
        "-u", "--update-db", nargs="?", const=True, default=False,
        help=""
    )
    argumentParser.add_argument(
        "-i", "--interval", default=1, type=int,
        help="File System Check interval (in days)"
    )

    return argumentParser.parse_args()


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    db_file = os.path.join(args.path, "FSCheck_db.json")

    # check if db file exists
    if not os.path.isfile(db_file) or args.update_db:
        try:
            FSCheck.exec(db_file)
        finally:
            sys.exit(UNKNOWN)

    check_file = os.path.join(args.path, "FSCheck.json")

    # check if check-file exists
    if not os.path.isfile(check_file):
        try:
            FSCheck.exec(check_file)
        finally:
            sys.exit(UNKNOWN)

    # load check file
    with open(check_file, "r") as file:
        check_data = json.load(file)

    # check date
    if date.today() - date.fromisoformat(check_data["DATE"]) > timedelta(days=args.interval):
        try:
            FSCheck.exec(check_file)
        finally:
            sys.exit(UNKNOWN)

    # load db data
    with open(db_file, "r") as file:
        db_data = json.load(file)

    returnCode = OK

    # calculate SUID diff
    suid_diff = set(check_data["SUID"]) - set(db_data["SUID"])

    if args.verbose:
        print(f"suid_diff={suid_diff}")

    if len(suid_diff) > 0:
        print(
            f"CRITICAL: {len(suid_diff)} new SUID Files detected: {suid_diff}")
        returnCode = CRITICAL

    # calculate SGID diff
    sgid_diff = set(check_data["SGID"]) - set(db_data["SGID"])

    if args.verbose:
        print(f"sgid_diff={sgid_diff}")

    if len(sgid_diff) > 0:
        print(
            f"CRITICAL: {len(sgid_diff)} new SGID Files detected: {sgid_diff}")
        returnCode = CRITICAL

    sys.exit(returnCode)


if __name__ == "__main__":
    main()
