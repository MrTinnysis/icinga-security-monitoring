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


def get_docker_cfg_path(filename: str) -> str:
    # cmd used to retrieve docker configuration
    cmd = f"systemctl show -p FragmentPath {filename}"

    try:
        path = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(
            f"UNKNOWN: Failed to retrieve docker config file path {filename}")
        sys.exit(UNKNOWN)

    # split KEY=value pairs and return value, also remove trailing newline char (\n)
    return path.split("=")[1][:-1]


def check_file_owner_permissions(path: str) -> bool:
    stats = os.stat(path)

    # check if user and group is set to root
    if stats.st_uid != 0 or stats.st_gid != 0:
        return False

    # get permissions from file stats
    permissions = stats.st_mode

    # check if owner has execute permission
    if permissions & stat.S_IXUSR:
        return False

    # check if group has execute or write permission
    if permissions & stat.S_IWGRP or permissions & stat.S_IXGRP:
        return False

    # check if others have execute or write permission
    if permissions & stat.S_IWOTH or permissions & stat.S_IXOTH:
        return False

    return True


def main() -> None:
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # get docker.service and docker.socket paths
    docker_srv = get_docker_cfg_path("docker.service")
    docker_soc = get_docker_cfg_path("docker.socket")

    if args.verbose:
        print(f"docker_service_path: {docker_srv}")
        print(f"docker_socket_path: {docker_soc}")

    returnCode = OK

    if os.path.isfile(docker_srv) and not check_file_owner_permissions(docker_srv):
        print(f"CRITICAL: 'docker.service' file owner/permission missmatch")
        returnCode = CRITICAL

    if os.path.isfile(docker_soc) and not check_file_owner_permissions(docker_soc):
        print(f"CRITICAL: 'docker.socket' file owner/permission missmatch")
        returnCode = CRITICAL

    if returnCode == OK:
        print(f"OK: docker file permissions set correctly")

    sys.exit(OK)


if __name__ == "__main__":
    main()
