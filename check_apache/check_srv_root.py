#!/usr/bin/env python3

import argparse
import sys
import os
import stat
import grp


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
        help='verbose output')
    argumentParser.add_argument(
        "-g", "--group", default="root",
        help="group to which the server files should belong")
    argumentParser.add_argument(
        "-r", '--srv-root', nargs="?", const="/usr/local/apache2", default=None,
        help='path to the apache ServerRoot\nDefaults to (Docker): /usr/local/apache2')
    argumentParser.add_argument(
        "-l", '--log', default="/var/log/apache2",
        help='path to the apache log folder\nDefaults to (Ubuntu): /var/log/apache2')
    argumentParser.add_argument(
        "-b", '--bin', default="/usr/sbin/apache2",
        help='path to the apache binary\nDefaults to (Ubuntu): /usr/sbin/apache2')
    argumentParser.add_argument(
        "-c", '--conf', default="/etc/apache2",
        help='path to the apache conf folder\nDefaults to (Ubuntu): /etc/apache2')
    argumentParser.add_argument(
        "-m", '--modules', default="/usr/lib/apache2",
        help='path to the apache modules folder\nDefaults to (Ubuntu): /usr/lib/apache2')

    return argumentParser.parse_args()


def check_stats(path, group, verbose=False):
    # Retrieves dir/file stats and checks against guidelines

    # convert groupname to group id
    groupid = grp.getgrnam(group).gr_gid

    # get file stats
    stats = os.stat(path)

    # Print path and stats if verbose output is enabled
    if verbose:
        print(f"Processing: {path}... ", end="")

    returnCode = OK

    # Check if owner or group differs from root (ID=0)
    if stats.st_uid != 0:
        print(f"WARNING: {path} Owner differs from root")
        returnCode = WARNING

    if (stats.st_gid != groupid):
        print(f"WARNING: {path} Group differs from {group}")
        returnCode = WARNING

    # Check if user differs from root and has write permissions
    if stats.st_uid != 0 and stats.st_mode & stat.S_IWUSR:
        print(
            f"CRITICAL: {path} Owner differs from root and has write permissions")
        returnCode = CRITICAL

    # Check if group has write permissions
    if (stats.st_mode & stat.S_IWGRP):
        print(f"CRITICAL: {path} Group has write permissions")
        returnCode = CRITICAL

    # Check if "everybody" has write permissions
    if (stats.st_mode & stat.S_IWOTH):
        print(f"CRITICAL: {path} 'Everybody' has write permissions")
        returnCode = CRITICAL

    if verbose and returnCode == OK:
        print("Ok.")

    return returnCode


def on_error(exception):
    print(f"CRITICAL: {exception.filename} doesn't exist")
    sys.exit(CRITICAL)


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # Maybe check if the configured path is indeed the server root (by checking httpd.conf)

    # start with returnCode OK
    returnCode = OK

    if not args.root:
        # Collect paths to relevant directories
        dirs_to_check = [args.bin, args.conf, args.log, args.modules]

    else:
        # Process ServerRoot
        returnCode = max(returnCode, check_stats(
            args.root, args.group, args.verbose))

        # Build absolute paths to subfolders that are being checked
        dirs_to_check = [os.path.join(args.root, dir)
                         for dir in ["bin", "conf", "logs", "modules"]]

    if args.verbose:
        print(f"dirs_to_check={dirs_to_check}")

    for dir in dirs_to_check:
        for root, _, files in os.walk(dir, onerror=on_error):
            returnCode = max(returnCode, check_stats(
                root, args.group, args.verbose))

            for name in files:
                returnCode = max(returnCode, check_stats(
                    os.path.join(root, name), args.group, args.verbose))

    if returnCode == OK:
        print("OK: ServerRoot Permission are ok.")

    sys.exit(returnCode)


if __name__ == "__main__":
    main()
