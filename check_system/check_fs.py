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
        "-wl", "--white-list", nargs="+", type=list, default=["btrfs", "cifs"],
        help="Specify a filesystem white list"
    )

    return argumentParser.parse_args()


def get_available_file_systems():
    # try:
    #     kernel_release = subprocess.check_output(
    #         "uname -r", shell=True).decode("utf-8")[0:-1]  # slice off trailing "\n"
    # except subprocess.CalledProcessError as ex:
    #     print("CRITICAL: failed to execute command: uname -r")
    #     sys.exit(CRITICAL)

    # fs_dir = f"/lib/modules/{kernel_release}/kernel/fs"

    # # The following folders do not contain filesystems
    blacklist = ["nls", "pstore", "cachefiles", "dlm", "fscache", "lockd", "nfs_common",
                 "nfsd", "quota", "binfmt_misc.ko"]

    # file_systems = []
    # # collect all kernel objects (.ko) files in fs_dir
    # for _, dirs, files in os.walk(fs_dir, followlinks=False):
    #     # remove blacklisted fs dirs
    #     for d in dirs:
    #         if d in blacklist:
    #             dirs.remove(d)

    #     # collect filesystem names
    #     for file in files:
    #         if file.endswith(".ko") and not file in blacklist:
    #             file_systems += [file[0:-3]]

    #     # file_systems += [file[0:-3]
    #     #                  for file in files if file.endswith(".ko") and not file in blacklist]

    # return file_systems

    cmd = "ls -l /lib/modules/$(uname -r)/kernel/fs"

    try:
        output = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"CRITICAL: failed to execute command: {cmd}")
        sys.exit(CRITICAL)

    file_systems = re.findall(
        r"\w{3} \d{2} \d{2}:\d{2} (.*?)$", output, flags=re.MULTILINE)

    return [fs for fs in file_systems if not fs in blacklist]


def _check(fs):
    cmd = f"modprobe -n -v '{fs}'"
    cmd2 = f"lsmod | grep '{fs}'"

    try:
        check1 = subprocess.check_output(cmd, shell=True).decode("utf-8")
        # dont check return code (because grep exists with return code 1 if nothing was found)
        check2 = subprocess.run(
            cmd2, shell=True, check=False, text=True, capture_output=True).stdout
    except subprocess.CalledProcessError as ex:
        print(f"CRITICAL: Failed to execute command {cmd}")
        print(ex)
        sys.exit(CRITICAL)

    return check1 in ["install /bin/true", "install /bin/false"] and check2 == ""


def check_fs_state(fs):
    mapping = {
        "fuse": ["cuse"],
        "overlayfs": ["overlay"],
        "fat": ["msdos"],
        "quota": ["quota_v1", "quota_v2"],
        "nfs": ["nfs", "nfsv2", "nfsv3", "nfsv4"],
        "afs": ["kafs"]
    }

    if fs in mapping:
        fs_list = mapping[fs]
    else:
        fs_list = [fs]

    return not all(map(_check, fs_list))


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
