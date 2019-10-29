#!/usr/bin/env python3

import argparse
import sys
import re

# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


def find_server_signature(httpd_conf):
    # Searches a "ServerSignature" Configuration Entry and returns the 
    # corresponding line, or None if no such Entry was found
    for line in httpd_conf:
        if "ServerSignature" in line:
            return line
    return None


def find_server_tokens(httpd_conf):
    # Searches a "ServerTokens" Configuration Entry and returns the
    # corresponding line, or None if no such Entry was found
    for line in httpd_conf:
        if "ServerTokens" in line:
            return line
    return None


def parse_args():
    # Parses the CLI Arguments and returns a dict containing the 
    # corresponding values
    argumentParser = argparse.ArgumentParser()

    argumentParser.add_argument(
        '-v', '--verbose', nargs="?", const=True, default=False,
        help='verbose output')
    argumentParser.add_argument(
        '--path', default="/usr/local/apache2/conf/httpd.conf",
        help='path to the httpd.conf configuration file')

    return argumentParser.parse_args()


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # TODO: Switch to ApacheConfig

    try:
        # open the configuration file
        with open(args.path, "r") as httpd_conf:
            # search entries in httpd_conf file
            server_sig = find_server_signature(httpd_conf)
            server_tokens = find_server_tokens(httpd_conf)
    except FileNotFoundError:
        # Abort if file could not be found
        print("CRITICAL: Config File Not Found")
        sys.exit(CRITICAL)

    # print the configured entries 
    if args.verbose:
        print(f"server_sig = {server_sig}")
        print(f"server_tokens = {server_tokens}")

    # check if either ServerSignature or ServerTokens config is missing
    if not server_sig or not server_tokens:
        print("CRITICAL: Missing Configuration for ServerSignature and/or ServerTokens")
        sys.exit(CRITICAL)

    # get configured values for server sig and server tokens
    match_sig = re.match("^ServerSignature (\w+)", server_sig)
    match_token = re.match("^ServerTokens (\w+)", server_tokens)

    # Abort if configured values could not be retrieved
    if not match_sig or not match_token:
        print("CRITICAL: Failed to read configuration (is it commented out?)")
        sys.exit(CRITICAL)

    # Compare the configured values with the suggested values
    if match_sig.group(1) != "Off" or match_token.group(1) != "Prod":
        print("WARNING: Potentially insecure configuration for ServerSignature and/or ServerTokens")
        print(f"Configured Value: {server_sig}, should be 'ServerSignature Off'")
        print(f"Configured Value: {server_tokens}, should be 'ServerTokens Prod'")
        sys.exit(WARNING)

    print("OK: Server Information hidden")
    sys.exit(OK)


if __name__ == "__main__":
    main()
