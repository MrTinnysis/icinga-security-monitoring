#!/usr/bin/env python3

import argparse
import sys
import subprocess
import json
from typing import List, Set


# monitoring plugin return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


def parse_args() -> Set:
    # Parses the CLI Arguments and returns a dict containing the
    # corresponding values
    argumentParser = argparse.ArgumentParser()

    argumentParser.add_argument(
        '-v', '--verbose', nargs="?", const=True, default=False,
        help='verbose output'
    )
    argumentParser.add_argument(
        "-w", "--whitelist", nargs="+", default=[], type=list,
        help="specify containers by name that should be ignored by this check"
    )

    return argumentParser.parse_args()


def get_docker_containers() -> List:
    cmd = "docker container ls --all --quiet"

    try:
        containers = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"UNKNOWN: Unable to retrieve docker container list")
        sys.exit(UNKNOWN)

    # remove last (empty) newline before returning list
    return containers.split("\n")[:-1]


def inspect_docker_containers(containers: List) -> List:
    cmd = f"docker container inspect {' '.join(containers)}"

    try:
        config = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"UNKNOWN: Unable to retrieve container configuration")
        sys.exit(UNKNOWN)

    # parse json output into python datastructures for further processing
    return json.loads(config)


def main() -> None:
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # get list of all docker containers (incl. not running)
    docker_containers = get_docker_containers()

    if args.verbose:
        print(f"docker_containers: {docker_containers}")

    # retrieve container configurations and remove whitelisted containers from list
    docker_container_configs = [cfg for cfg in inspect_docker_containers(
        docker_containers) if cfg.get("Name") not in args.whitelist]

    returnCode = OK

    for container_cfg in docker_container_configs:
        # retrieve mount options for root fs
        readonly_rootfs = container_cfg.get(
            "HostConfig", {}).get("ReadonlyRootfs", False)

        # get container name
        container_name = container_cfg.get("Name")

        if args.verbose:
            print(
                f"Container '{container_name}': readonly_rootfs: {readonly_rootfs}")

            # check if readonly rootfs option is set
            if not readonly_rootfs:
                print(
                    f"CRITICAL: Missing 'ReadonlyRootfs' flag on container '{container_name}'")
                returnCode = CRITICAL

    if returnCode == OK:
        print(f"OK: All 'no-new-privileges' flags set correctly")

    sys.exit(returnCode)


if __name__ == "__main__":
    main()
