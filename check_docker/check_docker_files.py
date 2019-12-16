#!/usr/bin/env python3

import argparse
import sys
import subprocess
import stat
import os

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


def get_docker_cfg_path(filename):
    cmd = f"systemctl show -p FragmentPath {filename}"

    try:
        path = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(
            f"UNKNOWN: Failed to retrieve docker config file path {filename}")
        sys.exit(UNKNOWN)

    # split KEY=value pairs and return value
    return path.split("=")[1]


def main() -> None:
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # get docker.service and docker.socket paths
    docker_srv = get_docker_cfg_path("docker.service")
    docker_soc = get_docker_cfg_path("docer.socket")

    if args.verbose:
        print(f"docker_service_path: {docker_srv}")
        print(f"docker_socket_path: {docker_soc}")


if __name__ == "__main__":
    main()
