#!/usr/bin/env python3

import requests
import argparse
import sys
import re
from requests.auth import HTTPBasicAuth
from datetime import datetime

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
    argumentParser.add_argument(
        '--apikey', metavar='APIKEY', nargs='+', type=str, default='',
        help='Certspotter API Key')

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

    apiURL = 'https://api.certspotter.com/v1/issuances?domain=' + arguments.domain + '&include_subdomains=true&match_wildcards=true&expand=issuer&expand=dns_names'
    apiKey = '22104_wWjXY2cQu4P8XwMGp9py'

    try:
        response = requests.get(apiURL, auth=HTTPBasicAuth(apiKey, ''))

        certCount = 0
        for cert in response.json():
            if arguments.verbose:
                print(cert)

            certCount += 1
            issuerOrganisationName = re.findall('O=(.*),', cert['issuer']['name'])[0]
            validUntil = cert['not_after']
            if issuerOrganisationName not in arguments.issuer:
                criticalCount += 1
                status += ' ' + issuerOrganisationName + ' is not in whitelist!;'

            if not validUntil:
                warningCount += 1
                status += ' expired;'

        if criticalCount > 0:
            returnCode = CRITICAL
            status = 'CRITICAL:' + status
        elif warningCount > 0:
            returnCode = WARNING
            status = 'WARNING:' + status
        else:
            returnCode = OK
            status = 'OK: All found issuers are whitelisted and no expiring Certificates found.'

        performanceData = ' | cert_count=' + str(certCount)

    except Exception as e:
        returnCode = CRITICAL
        status = ('CRITICAL: ' + str(e))

    print(status + performanceData)
    sys.exit(returnCode)


if __name__ == '__main__':
    main()
