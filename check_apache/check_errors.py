#!/usr/bin/env python3

import argparse
import sys
import os

# https://pypi.org/project/apache-log-parser/1.7.0/
import apache_log_parser as alp


# https://pypi.org/project/parse_apache_configs/
# https://github.com/etingof/apacheconfig


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
        help='verbose output')
    argumentParser.add_argument(
        "-c", "--config", default="/etc/apache2/apache2.conf",
        help=""
    )

    return argumentParser.parse_args()


def get_log_formats(config):
    return [line for line in config if "LogFormat" in line]


def get_log_dirs(config):
    error_log_dir = None
    custom_log_dir = None
    for line in config:
        if "ErrorLog" in line:
            error_log_dir = line

        if "CustomLog" in line:
            custom_log_dir = line

    return (error_log_dir, custom_log_dir)


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

    with open(args.config, "r") as file:
        log_dirs = get_log_dirs(file)
        log_formats = get_log_formats(file)

    if None in log_dirs or len(log_formats) == 0:
        print(f"CRITICAL: Failed to read config {args.config}")

    parser = alp.Parser("")


if __name__ == "__main__":
    main()
