#!/usr/bin/env python3

import argparse
import sys
import re
import os

from ApacheConfig import ApacheConfig

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
        '-v', '--verbose', nargs="?", const=True, default=False,
        help='verbose output'
    )
    argumentParser.add_argument(
        "-p", "--path", default="/etc/apache2/apache2.conf",
        help="path to the configuration file"
    )
    argumentParser.add_argument(
        "-e", "--env", nargs="?", const="/etc/apache2/envvars", default=None,
        help="path to the environment variables file"
    )
    argumentParser.add_argument(
        "-vh", "--vhost", default=None,
        help="virtual host whose config should be loaded (if any)"
    )

    return argumentParser.parse_args()


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    if not os.path.isfile(args.path):
        print(f"CRITICAL: {args.path} does not denote a file!")
        sys.exit(CRITICAL)

    if args.env and not os.path.isfile(args.env):
        print(f"CRITICAL: {args.env} does not denote a file!")
        sys.exit(CRITICAL)

    config = ApacheConfig(args.path, env_var_file=args.env)

    server_sig = config.get("ServerSignature", args.vhost)
    server_tokens = config.get("ServerTokens", args.vhost)

    # print the configured entries
    if args.verbose:
        print(f"server_sig = {server_sig}")
        print(f"server_tokens = {server_tokens}")

    # check if either ServerSignature or ServerTokens config is missing
    if not server_sig or not server_tokens:
        print("CRITICAL: Missing Configuration for ServerSignature and/or ServerTokens")
        sys.exit(CRITICAL)

    if server_sig != "Off" or server_tokens != "Prod":
        print("WARNING: Potentially insecure configuration for ServerSignature and/or ServerTokens")
        print(
            f"Configured Value: 'ServerSignature {server_sig}', should be 'ServerSignature Off'")
        print(
            f"Configured Value: 'ServerTokens {server_tokens}', should be 'ServerTokens Prod'")
        sys.exit(WARNING)

    print("OK: Server Information hidden")
    sys.exit(OK)


if __name__ == "__main__":
    main()
