#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess
import re

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
        "-wl", "--white-list", nargs="+", type=list, default=["fat", "btrfs", "cifs"],
        help="Specify a filesystem white list"
    )

    return argumentParser.parse_args()


def get_available_file_systems():
    cmd = "ls -l /lib/modules/$(uname -r)/kernel/fs"

    try:
        output = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"CRITICAL: failed to execute command: {cmd}")
        sys.exit(CRITICAL)
    else:
        file_systems = []
        regex = re.compile(" (.*?)$")

        for line in output.split("\n"):
            match = regex.match(line)
            if match:
                file_systems += [match.group(1)]

        return file_systems


def check_fs_state(fs):
    cmd = "modprobe -n -v " + fs
    cmd2 = "lsmod | grep " + fs

    try:
        check_1 = subprocess.check_output(cmd, shell=True).decode("utf-8")
        check_2 = subprocess.check_output(cmd2, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"CRITICAL: Failed to execute commands {cmd}, {cmd2}")
        sys.exit(CRITICAL)
    else:
        return check_1 == ("install /bin/true" or check_1 == "install /bin/false") and check_2 == ""


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # get all filesystems that are installed on the system
    file_systems = get_available_file_systems()

    if args.verbose:
        print(f"Filesystems found: {file_systems}")

    # filter by whitelist
    filtered_file_systems = [
        fs for fs in file_systems if not fs in args.white_list]

    if args.verbose:
        print(f"Filtered File Systems: {filtered_file_systems}")

    # filter by "enabled" state
    enabled_file_systems = [
        fs for fs in filtered_file_systems if check_fs_state(fs)]

    if args.verbose:
        print(f"Enabled File Systems: {enabled_file_systems}")

    if len(enabled_file_systems) > 0:
        print(
            f"WARNING: The following filesystems should be disabled: {enabled_file_systems}")
        sys.exit(WARNING)

    print("OK: all unused filesystems disabled")
    sys.exit(OK)


if __name__ == "__main__":
    main()
