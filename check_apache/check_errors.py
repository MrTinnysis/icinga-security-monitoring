#!/usr/bin/env python3

import argparse
import sys
import os
import re

# https://pypi.org/project/apache-log-parser/1.7.0/
import apache_log_parser as alp

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
        help="specify the config file that should be loaded (used to locate corresponding log files)"
    )
    argumentParser.add_argument(
        "-e", "--env", nargs="?", const="/etc/apache2/envvars", default=None,
        help="specify the environment variables file to load (used to parse the config file)"
    )
    argumentParser.add_argument(
        "-vh", "--vhost", default=None,
        help="specify the virtual host whose config should be loaded (if any)"
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

    if args.verbose:
        print(f"config={config}")

    error_log = config.get("ErrorLog", vhost=args.vhost)
    custom_log = config.get("CustomLog", vhost=args.vhost)
    log_formats = config.get("LogFormat", vhost=args.vhost)

    if args.verbose:
        print(f"error_log={error_log}")
        print(f"custom_log={custom_log}")
        print(f"log_formats={log_formats}")

    # TODO
    parser = alp.Parser("")


if __name__ == "__main__":
    main()
