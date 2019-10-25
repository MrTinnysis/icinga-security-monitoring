#!/usr/bin/env python3

import argparse, sys, os, stat


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
		'--path', default="/usr/local/apache2",
		help='path to the ServerRoot')

    return argumentParser.parse_args()

def check_stats(path, verbose=False):
    # Retrieves dir/file stats and checks against guidelines

    # get file stats
    stats = os.stat(path)

    # Print path and stats if verbose output is enabled
    if verbose:
        print(f"Processing: {path}... ", end="")

    returnCode = OK

    # Check if owner or group differs from root (ID=0)
    if stats.st_uid != 0 or stats.st_gid != 0:
        print(f"WARNING: {path} Owner or Group differs from root")
        returnCode = WARNING

    # Check if user differs from root and has write permissions
    if stats.st_uid != 0 and stats.st_mode & stat.S_IWUSR:
        print(f"CRITICAL: {path} Owner differs from root and has write permissions")
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


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # Check if configured path denotes a directory
    if not os.path.isdir(args.path):
        print("CRITICAL: The configured path does not denote a directory!")
        sys.exit(CRITICAL)

    # Maybe check if the configured path is indeed the server root (by checking httpd.conf)

    # start with returnCode OK
    returnCode = OK

    # Process ServerRoot
    returnCode = max(returnCode, check_stats(args.path, args.verbose))

    # Build absolute paths to subfolders that are being checked
    dirs_to_check = [os.path.join(args.path, dir) for dir in ["bin", "conf", "logs"]]

    # Print absolute paths if verbose output is enabled
    if args.verbose:
        print(f"dirs_to_check = {dirs_to_check}")

    # Process every subfolder and update returnCode 
    for dir in dirs_to_check:
        # recursively process all subfolders and files
        for root, _, files in os.walk(dir):
            # check folder itself
            returnCode = max(returnCode, check_stats(root, args.verbose))

            # check every file in folder
            for name in files:
                returnCode = max(returnCode, check_stats(os.path.join(root, name), args.verbose))

    
    sys.exit(returnCode)


if __name__=="__main__":
	main()