#!/usr/bin/env python3

import argparse
import sys
import os
import re

# https://github.com/rory/apache-log-parser
# https://pypi.org/project/apache-log-parser/1.7.0/
import apache_log_parser

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
        print(config)

    log_format_list = config.get("LogFormat", vhost=args.vhost)
    custom_log = config.get("CustomLog", vhost=args.vhost)

    # convert format to list if only one format is configured
    if type(log_format_list) != list:
        log_format_list = [log_format_list]

    if args.verbose:
        print(f"log_format_list={log_format_list}")
        print(f"custom_log={custom_log}")

    if not log_format_list:
        print("CRITICAL: Not log format specified")
        sys.exit(CRITICAL)

    # CustomLog definition consists of path and either "nickname" or format string
    match = re.match("(.+?) (.+)", custom_log)

    # Check format
    if not match:
        print(f"CRITICAL: Invalid CustomLog configuration {custom_log}")
        sys.exit(CRITICAL)

    # set log_file to be the path
    log_file = match.group(1)

    # check if nickname/format (format strings are contained in "")
    if match.group(2)[0] == '"' and match.group(2)[-1] == '"':
        # if '%' in match.group(2):
        # format string (remove "")
        print("format string")
        #log_format = match.group(2)[1:-1]
        log_format = match.group(2).strip('"')
    else:
        # nickname
        print("nickname")
        log_format = find_logformat_by_nickname(
            log_format_list, match.group(2))

    if args.verbose:
        print(f"log_file={log_file}")
        print(f"log_format={log_format}")

    if not os.path.isfile(log_file):
        print(
            f"CRITICAL: The configured CustomLog path does not denote a file: {log_file}")
        sys.exit(CRITICAL)

    # error_log_format = config.get("ErrorLogFormat", vhost=args.vhost)
    # error_log = config.get("ErrorLog", vhost=args.vhost)

    # if not error_log_format:
    #     # set default error log format
    #     error_log_format = "[%{u}t] [%m:%l] [pid %P:tid %T] %M"

    # if args.verbose:
    #     print(f"error_log_format={error_log_format}")
    #     print(f"error_log={error_log}")

    # if not os.path.isfile(error_log):
    #     print("CRITICAL: The configured ErrorLog path does not denote a file!")
    #     sys.exit(CRITICAL)

    # parser = apache_log_parser.make_parser(error_log_format)

    # with open(error_log, "r") as file:
    #     # checking the whole file might not be a goot idea...
    #     log_data = [parser(line) for line in file]

    # print(log_data)


def find_logformat_by_nickname(log_format_list, nickname):
    regex = re.compile(f'"(.+)" {nickname}$')
    for log_format in log_format_list:
        match = regex.match(log_format)
        if match:
            return match.group(1)
    print(f"CRITICAL: Could not find LogFormat {nickname}")
    sys.exit(CRITICAL)


if __name__ == "__main__":
    main()
