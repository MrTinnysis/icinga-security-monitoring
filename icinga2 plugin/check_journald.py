#!/bin/python

import sys, argparse

# monitoring return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

# defaults
returnCode = UNKNOWN

# parse arguments
argumentParser = argparse.ArgumentParser()
argumentParser.add_argument(
    '-h', '--hostname', default='localhost',
    help='host with systemd journal gateway (default "localhost")')
argumentParser.add_argument(
    '-p', '--port', default='19531',
    help='the gateway port (default "19531")')

arguments = argumentParser.parse_args()

sys.exit(returnCode)
