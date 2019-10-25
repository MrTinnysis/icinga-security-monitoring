#!/usr/bin/env python3

import argparse, sys


def find_server_signature(httpd_conf):
    for line in httpd_conf:
        if "ServerSignature" in line:
            return line
    return None


def find_server_tokens(httpd_conf):
    for line in httpd_conf:
        if "ServerTokens" in line:
            return line
    return None


def parse_args():
    argumentParser = argparse.ArgumentParser()

    argumentParser.add_argument(
		'-v', '--verbose', nargs="?", const=True, default=False,
		help='verbose output')
    argumentParser.add_argument(
		'--path', default="/usr/local/apache2/conf/httpd.conf",
		help='path to the httpd.conf configuration file')

    return argumentParser.parse_args()


def main():
    # monitoring plugin return codes
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3

    args = parse_args()

    if args.verbose:
        print(args)

    returnCode = OK

    try:
        with open(args.path, "r") as httpd_conf:
            # search entries in https_conf file
            server_sig = find_server_signature(httpd_conf)
            server_tokens = find_server_tokens(httpd_conf)
    except FileNotFoundError:
        print("CRITICAL: Config File Not Found")
        returnCode = CRITICAL

    # check if either ServerSignature or ServerTokens config is missing
    if server_sig is None or server_tokens is None:
        print("CRITICAL: Missing Configuration for ServerSignature and/or ServerTokens")
        returnCode = CRITICAL

    # check if either ServerSignature or ServerTokens is configured wrong
    if server_sig != "ServerSignature Off" or server_tokens != "ServerTokens Prod":
        print("WARNING: Potentially insecure configuration for ServerSignature and/or ServerTokens")
        returnCode = max(returnCode, WARNING)

    sys.exit(returnCode)


if __name__=="__main__":
	main()