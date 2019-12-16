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


def get_docker_networks() -> list:
    cmd = "docker network ls --quiet"

    try:
        networks = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"UNKNOWN: Unable to retrieve docker network list")
        sys.exit(UNKNOWN)

    # remove last (empty) newline before returning list
    return networks.split("\n")[:-1]


def inspect_docker_networks(networks: list) -> list:
    cmd = f"docker network inspect {' '.join(networks)}"

    try:
        config = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(
            f"UNKNOWN: Unable to retrieve network configuration")
        sys.exit(UNKNOWN)

    # parse json output into python datastructures before for further processing
    return json.loads(config)


def main() -> None:
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

    # get network configurations
    network_configs = inspect_docker_networks(docker_networks)

    # retrieve all networks that use the host driver
    host_networks = [
        network for network in network_configs if network["Driver"] == "host"]

    # retrieve all networks that use the macvlan driver
    macvlan_networks = [
        network for network in network_configs if network["Driver"] == "macvlan"]

    returnCode = OK

    # check if there are any containers using the host networks
    for network in host_networks:
        containers = network.get("Containers", [])

        if len(containers) > 0:
            print(
                f"CRITICAL: {len(containers)} container(s) are using the host network {network['Name']}")
            returnCode = CRITICAL

    for network in macvlan_networks:
        containers = network.get("Containers", [])

        if len(containers) > 0:
            print(
                f"CRITICAL: {len(containers)} container(s) are using the macvlan network {network['Name']}")
            returnCode = CRITICAL

    if returnCode == OK:
        print(f"OK: No containers using host/macvlan networks found.")

    sys.exit(returnCode)


if __name__ == "__main__":
    main()
