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
        "-c", "--config", default="/etc/apache2/apache2.conf",
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
    argumentParser.add_argument(
        "-l", "--level", default="medium",
        help="no ciphers below this level allowed"
    )

    return argumentParser.parse_args()


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    if not os.path.isfile(args.config):
        print(f"CRITICAL: {args.config} does not denote a file!")
        sys.exit(CRITICAL)

    if args.env and not os.path.isfile(args.env):
        print(f"CRITICAL: {args.env} does not denote a file!")
        sys.exit(CRITICAL)

    config = ApacheConfig(args.config, env_var_file=args.env)

    sslciphersuite = config.get("SSLCipherSuite", args.vhost)


    # print the configured entries
    if args.verbose:
        print(f"server_sig = {sslciphersuite}")

    # check if config is missing
    if not sslciphersuite:
        print("CRITICAL: Missing Configuration for SSLCipherSuite")
        sys.exit(CRITICAL)

    if 'NULL' in sslciphersuite :
        print("CRITICAL: Allowed NULL Ciphers in Configuration for SSLCipherSuite")
        sys.exit(CRITICAL)

    print("OK: no NULL ciphers and ciphers blow medium configured!")
    sys.exit(OK)


if __name__ == "__main__":
    main()
