#!/usr/bin/env python3

import sys
import argparse

# SSLLabs API from https://github.com/takeshixx/python-ssllabs
from ssllabs import SSLLabsAssessment

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
    argumentParser.add_argument(
        '--warning', metavar='GRADE', type=str, default='A',
        help='return warning if grade is below')
    argumentParser.add_argument(
        '--critical', metavar='GRADE', type=str, default='B',
        help='return critical if grade is below')
    argumentParser.add_argument(
        '--host', metavar='HOST', type=str, required=True,
        help='external reachable host to check')
    argumentParser.add_argument(
        '--max-age', metavar='NUMBER', type=int, default=5,
        help='max age (in hours) of cached check result')

    return argumentParser.parse_args()


def main():

    # defaults
    returnCode = UNKNOWN
    grading = {'A++': 0, 'A+': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5, 'E': 6, 'F': 7, 'T': 9}
    warningCount = 0
    criticalCount = 0
    status = ''

    # parse CLI Arguments
    arguments = parse_args()

    try:
        assessment = SSLLabsAssessment(host=arguments.host)
        info = assessment.analyze(
            ignore_mismatch='on',
            from_cache='on',
            max_age=arguments.max_age,
            return_all='done',
            publish='off',
            resume=False,
            detail=False)

        for endpoint in info['endpoints']:
            if grading[endpoint['grade']] > grading[arguments.critical]:
                criticalCount += 1
                status += 'CRITICAL: '
            elif grading[endpoint['grade']] > grading[arguments.warning]:
                warningCount += 1
                status += 'WARNING: '
            else:
                status += 'OK: '

            status += ('ServerName: ' + endpoint['serverName'] +
                       ' IPAddress: ' + endpoint['ipAddress'] +
                       ' Grade: ' + endpoint['grade'] + ';')

    except Exception as e:
        status = ('CRITICAL: ' + str(e))

    print(status)
    if criticalCount > 0:
        returnCode = CRITICAL
    elif warningCount > 1:
        returnCode = WARNING
    else:
        returnCode = OK
    sys.exit(returnCode)


if __name__ == '__main__':
    main()
