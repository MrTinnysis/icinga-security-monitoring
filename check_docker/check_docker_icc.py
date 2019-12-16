#!/usr/bin/env python3

import argparse
import sys
import subprocess
import json
from pprint import pprint


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


def inspect_docker_networks(networks: list):
    cmd = f"docker network inspect {' '.join(networks)}"

    try:
        config = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(
            f"UNKNOWN: Unable to retrieve network configuration")
        sys.exit(UNKNOWN)

    return json.loads(config)


def get_default_bridge(networks: list):
    default_bridge_option = "com.docker.network.bridge.default_bridge"

    # retrieve network configurations for each network
    network_configs = inspect_docker_networks(networks)

    for network in network_configs:
        # check if network options contain an entry for default bridge
        options = network["Options"]

        if default_bridge_option in options and options[default_bridge_option] == "true":
            return network

    # if this point is reached, then there was no default bridge configured
    print("UNKNOWN: No default bridge configuration found...")
    sys.exit(UNKNOWN)


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # get a list of all configured docker networks
    docker_networks = get_docker_networks()

    if args.verbose:
        print(f"docker_networks: {docker_networks}")

    # get the default bridge
    default_bridge = get_default_bridge(docker_networks)

    if args.verbose:
        print("default_bridge:")
        pprint(default_bridge)

    # check if icc is enabled
    enable_icc = default_bridge["Options"]["com.docker.network.bridge.enable_icc"]

    if enable_icc != "true":
        print(f"OK: Inter-container communication (icc) disabled")
        sys.exit(OK)

    # icc not disabled -> check if there are any containers on the default bridge

    # get all containers that run on the default bridge (if any)
    containers = default_bridge.get("Containers", [])

    if len(containers) > 1:
        print(
            f"CRITICAL: {len(containers)} containers running on the default bridge with icc enabled!")
        sys.exit(CRITICAL)

    elif len(containers) == 1:
        print(f"WARNING: 1 container running on the default bridge with icc enabled!")
        sys.exit(WARNING)

    else:
        print(f"OK: There are no containers running on the default bridge")
        sys.exit(OK)


if __name__ == "__main__":
    main()
