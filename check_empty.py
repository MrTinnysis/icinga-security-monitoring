#!/usr/bin/env python3

import sys
import argparse

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
        '-v', '--verbose', nargs='?', const=True, default=False,
        help='verbose output')
    argumentParser.add_argument(
        '-w', '--warning', metavar='LEVEL', type=str, default='?',
        help='return warning if check result is below or above')
    argumentParser.add_argument(
        '-c', '--critical', metavar='LEVEL', type=str, default='?',
        help='return critical if check result is below or above')

    return argumentParser.parse_args()


def main():

    # defaults
    returnCode = UNKNOWN
    status = ''
    performanceData = ''

    # parse CLI Arguments
    arguments = parse_args()

    # do some stuff here

    print(status + ' | ' + performanceData)
    sys.exit(returnCode)


if __name__ == '__main__':
    main()
