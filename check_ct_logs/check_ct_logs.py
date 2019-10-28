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
    argumentParser.add_argument(
        '--domain', metavar='DOMAIN', type=str, required=True,
        help='domain to search in certificate transparency logs')
    argumentParser.add_argument(
        '--issuer', metavar='ISSUER ORGANISATION NAME', nargs='+', type=str, required=True,
        help='whitelist issuers')

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

    try:

        response = requests.get(
            'https://api.certspotter.com/v1/issuances',
            params=b'domain=bfh.ch&expand=dns_names&expand=issuer')

        certCount = 0
        for cert in response.json():
            certCount += 1
            issuerOrganisationName = re.findall('O=(.*),', cert['issuer']['name'])[0]
            if issuerOrganisationName not in arguments.issuer:
                criticalCount += 1
                status += 'CRITICAL: ' + issuerOrganisationName + 'is not in whitelist!;'

        if criticalCount > 0:
            returnCode = CRITICAL
        else:
            returnCode = OK
            status = 'OK: All found issuers are whitelisted.'

        performanceData = ' | cert_count=' + str(certCount)

    except Exception as e:
        status = ('CRITICAL: ' + str(e))

    print(status + performanceData)
    sys.exit(returnCode)


if __name__ == '__main__':
    main()
