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

    config = ApacheConfig(args.path, env_var_file=args.env)

    if args.verbose:
        print(f"config={config}")

    # config = get_apache_config(
    #     args.config, env_vars=args.env, verbose=args.verbose)

    # if args.vhost != None:
    #     vhosts = config.get("VirtualHost")

    #     if type(vhosts) == list:
    #         vhost_cfg = next(
    #             (vh[args.vhost] for vh in vhosts if vh.get(args.vhost) != None), None)
    #     else:
    #         vhost_cfg = vhosts.get(args.vhost)

    #     if not vhost_cfg:
    #         print(f"CRITICAL: Could not find VirtualHost Config {args.vhost}")
    #         sys.exit(CRITICAL)

    #     error_log = vhost_cfg.get("ErrorLog")
    #     custom_log = vhost_cfg.get("CustomLog")
    #     log_formats = vhost_cfg.get("LogFormat")

    # error_log = error_log if args.vhost and error_log else config.get(
    #     "ErrorLog")
    # custom_log = custom_log if args.vhost and custom_log else config.get(
    #     "CustomLog")
    # log_formats = log_formats if args.vhost and log_formats else config.get(
    #     "LogFormat")

    # if args.verbose:
    #     print(f"error_log={error_log}")
    #     print(f"custom_log={custom_log}")
    #     print(f"log_formats={log_formats}")

    parser = alp.Parser("")


if __name__ == "__main__":
    main()
