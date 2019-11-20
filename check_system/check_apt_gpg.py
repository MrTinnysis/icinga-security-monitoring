#!/usr/bin/env python3

import requests
import argparse
import sys
import re

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
        '--verbose', nargs='?', const=True, default=False,
        help='verbose output')

    return argumentParser.parse_args()


def main():

    # defaults
    returnCode = UNKNOWN
    status = ''
    performanceData = ''
    warningCount = 0
    criticalCount = 0

    # parse CLI Arguments
    arguments = parse_args()

    print(status + performanceData)
    sys.exit(returnCode)

    cmd = "apt-key list"

    try:
        # execute shell commands to retrieve server version
        server_version = subprocess.check_output(
            cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"CRITICAL: Failed to execute shell command: {cmd}")
        sys.exit(CRITICAL)

    response = requests.get('https://download.docker.com/linux/ubuntu/gpg')


if __name__ == '__main__':
    main()
