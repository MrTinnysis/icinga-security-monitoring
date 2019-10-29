#!/usr/bin/env python3

import argparse
import sys
import os
import re

# https://pypi.org/project/apache-log-parser/1.7.0/
import apache_log_parser as alp

from ApacheConfig import get_apache_config


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


# def parse_env_vars(env_var, verbose=False):
#     suffix = ""
#     output = {}
#     regex = re.compile("^export (.*)=(.*)$")
#     with open(env_var, "r") as file:
#         for line in file:
#             # Suffixes currently not supported...
#             # match = re.match("SUFFIX=(.*)")
#             # if "SUFFIX=" in line:
#             #     pass

#             match = regex.match(line)

#             if match:
#                 output[match.group(1)] = match.group(
#                     2).replace("$SUFFIX", suffix)

#     if verbose:
#         print(output)

#     return output


# def parse_apache_config(path, env_var=None, verbose=False):
#     if env_var:
#         env_var = parse_env_vars(env_var, verbose)


#     options = {
#         "useapacheinclude": True,
#         "includerelative": True,
#         "includedirectories": True,
#         "configpath": [path]
#     }

#     with apacheconfig.make_loader(**options) as loader:
#         config = loader.load(path)

#     if verbose:
#         print(config)

#     return config


# def get_log_formats(config):
#     return [line for line in config if "LogFormat" in line]


# def get_log_dirs(config):
#     error_log_dir = None
#     custom_log_dir = None
#     for line in config:
#         if "ErrorLog" in line:
#             error_log_dir = line

#         if "CustomLog" in line:
#             custom_log_dir = line

#     return (error_log_dir, custom_log_dir)


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

    config = get_apache_config(
        args.config, env_vars=args.env, verbose=args.verbose)

    if args.vhost != None:
        vhosts = config.get("VirtualHost")

        if type(vhosts) == list:
            vhost_cfg = next(
                (vh for vh in vhosts if vh[0] == args.vhost), None)
        else:
            print(type(vhosts))
            vhost_cfg = vhosts if vhosts[0] == args.vhost else None

        if not vhost_cfg:
            print(f"CRITICAL: Could not find VirtualHost Config {args.vhost}")
            sys.exit(CRITICAL)

        error_log = vhost_cfg.get("ErrorLog")
        custom_log = vhost_cfg.get("CustomLog")
        log_formats = vhost_cfg.get("LogFormat")

    error_log = error_log if args.vhost and error_log else config.get(
        "ErrorLog")
    custom_log = custom_log if args.vhost and custom_log else config.get(
        "CustomLog")
    log_formats = log_formats if args.vhost and custom_log else config.get(
        "LogFormat")

    if args.verbose:
        print(f"error_log={error_log}")
        print(f"custom_log={custom_log}")
        print(f"log_formats={log_formats}")

    # with open(args.config, "r") as file:
    #     log_dirs = get_log_dirs(file)
    #     log_formats = get_log_formats(file)

    # if None in log_dirs or len(log_formats) == 0:
    #     print(f"CRITICAL: Failed to read config {args.config}")

    parser = alp.Parser("")


if __name__ == "__main__":
    main()
