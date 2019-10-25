#!/usr/bin/env python3

import argparse, sys, re


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

    try:
        with open(args.path, "r") as httpd_conf:
            # search entries in https_conf file
            server_sig = find_server_signature(httpd_conf)
            server_tokens = find_server_tokens(httpd_conf)
    except FileNotFoundError:
        print("CRITICAL: Config File Not Found")
        sys.exit(CRITICAL)

    if args.verbose:
        print(f"server_sig = {server_sig}")
        print(f"server_tokens = {server_tokens}")

    # check if either ServerSignature or ServerTokens config is missing
    if not server_sig or not server_tokens:
        print("CRITICAL: Missing Configuration for ServerSignature and/or ServerTokens")
        sys.exit(CRITICAL)

    # get configured values for server sig and server tokens
    match_sig = re.fullmatch("ServerSignature (\w+)", server_sig)
    match_token = re.fullmatch("ServerTokens (\w+)", server_tokens)

    if not match_sig  or not match_token:
        print("CRITICAL: Could not retrieve configured values")
        sys.exit(CRITICAL)

    if match_sig.group(1) != "Off" or match_token.group(1) != "Prod":
        print("WARNING: Potentially insecure configuration for ServerSignature and/or ServerTokens")
        sys.exit(WARNING)

    sys.exit(OK)


if __name__=="__main__":
	main()