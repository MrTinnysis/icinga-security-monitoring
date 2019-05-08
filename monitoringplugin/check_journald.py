#!/bin/python

import re, sys, argparse

# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

# defaults
returnCode = UNKNOWN


# define period
def period(string):
    if not re.search("^[1-9]{1,2}[m,h,d]$", string):
        msg = "%r is not a valid period" % string
        raise argparse.ArgumentTypeError(msg)
    return string


# parse arguments
argumentParser = argparse.ArgumentParser()

argumentParser.add_argument(
    '-v', '--verbose', default=False,
    help='verbose output')
argumentParser.add_argument(
    '-w', '--warning', metavar='RANGE', default='',
    help='return warning if count of found logs is outside RANGE')
argumentParser.add_argument(
    '-c', '--critical', metavar='RANGE', default='',
    help='return critical if count of found logs is outside RANGE')
argumentParser.add_argument(
    '--hostname', metavar='HOST', default='localhost',
    help='host with systemd journal gateway or localhost for direct access (default "localhost")')
argumentParser.add_argument(
    '--port', metavar='NUMBER', default='19531',
    help='the gateway port (default "19531")')
argumentParser.add_argument(
    '--path', default='',
    help='path to journal log folder')
argumentParser.add_argument(
    '--matches', nargs='+',
    help='matches for logparse')
argumentParser.add_argument(
    '--period', metavar='NUMBER', default='1h', type=period,
    help='check log of last period - format 90m')

arguments = argumentParser.parse_args()

print(arguments)

sys.exit(returnCode)
