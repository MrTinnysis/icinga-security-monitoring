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
        help='Verbose output')
    argumentParser.add_argument(
        "-g", "--group", default="root",
        help="Group to which the server files should belong")
    argumentParser.add_argument(
        "-r", '--srv-root', nargs="?", const="/usr/local/apache2", default=None,
        help='Path to the apache ServerRoot, Defaults to (Docker): /usr/local/apache2')
    argumentParser.add_argument(
        "-s", "--skip", nargs="+", default=["htdocs"],
        help="Specify which subfolders in the ServerRoot should be skipped (only effective with option '-r')")
    argumentParser.add_argument(
        "-p", "--paths", nargs="+", default=["/var/log/apache2", "/usr/sbin/apache2",
                                             "/etc/apache2", "/usr/lib/apache2"],
        help="""
                Specify which files/folders should be checked. Usually this will be at least the 
                following folders: logs, binaries, libs/modules and config. Defaults to the 
                Ubuntu/Debian locations, which are as follows: logs=/var/log/apache2, binaries=/usr/sbin/apache2, 
                libs/modules=/usr/lib/apache2, config=/etc/apache2.
             """
    )

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

    # start with returnCode OK
    returnCode = OK

    # check if server root is specified
    if args.srv_root:
        # Check if configured path denotes a directory
        if not os.path.isdir(args.srv_root):
            print("CRITICAL: The configured path does not denote a directory!")
            sys.exit(CRITICAL)

        # Process ServerRoot and all subdirs
        for root, dirs, files in os.walk(args.srv_root, followlinks=True):
            # Process the current directory
            returnCode = max(returnCode, check_stats(
                root, args.group, args.verbose))

            # skip blacklisted directories
            for i, name in enumerate(dirs):
                if name in args.skip:
                    del dirs[i]

            # Process all files in the current directory
            for name in files:
                returnCode = max(returnCode, check_stats(
                    os.path.join(root, name), args.group, args.verbose))

    else:
        # Collect all files/dirs that should be checked
        dirs_to_check = [args.bin, args.conf, args.log, args.modules]

    # if not args.srv_root:
    #     # Collect paths to relevant directories
    #     dirs_to_check = [args.bin, args.conf, args.log, args.modules]

    # else:
    #     # Check if configured path denotes a directory
    #     if not os.path.isdir(args.srv_root):
    #         print("CRITICAL: The configured path does not denote a directory!")
    #         sys.exit(CRITICAL)

    #     # Process ServerRoot
    #     returnCode = max(returnCode, check_stats(
    #         args.srv_root, args.group, args.verbose))

    #     # Build absolute paths to subfolders that are being checked
    #     dirs_to_check = [os.path.join(args.srv_root, dir)
    #                      for dir in ["bin", "conf", "logs", "modules"]]

    # if args.verbose:
    #     print(f"dirs_to_check={dirs_to_check}")

    # for dir in dirs_to_check:
    #     for root, _, files in os.walk(dir, onerror=on_error, followlinks=True):
    #         returnCode = max(returnCode, check_stats(
    #             root, args.group, args.verbose))

    #         for name in files:
    #             returnCode = max(returnCode, check_stats(
    #                 os.path.join(root, name), args.group, args.verbose))

    if returnCode == OK:
        print("OK: ServerRoot Permission are ok.")

    sys.exit(returnCode)


if __name__ == "__main__":
    main()
