#!/usr/bin/env python3

import argparse
import sys
import subprocess
import json


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

    return networks.split("\n")[:-1]


def inspect_docker_network(network):
    cmd = f"docker network inspect {network}"

    try:
        config = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(
            f"UNKNOWN: Unable to retrieve network configuration (net_id: {network})")
        sys.exit(UNKNOWN)

    return json.loads(config)[0]


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

    for network in docker_networks:
        network_config = inspect_docker_network(network)
        print(network_config)


if __name__ == "__main__":
    main()
