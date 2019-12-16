#!/usr/bin/env python3

import argparse
import sys
import re
import subprocess


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

    return argumentParser.parse_args()


def get_docker_networks():
    cmd = "docker network ls --quiet"

    try:
        networks = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"UNKNOWN: Unable to retrieve docker network list")
        sys.exit(UNKNOWN)

    return networks.split("\n")


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    docker_networks = get_docker_networks()

    if args.verbose:
        print(f"docker_networks: {docker_networks}")


if __name__ == "__main__":
    main()
