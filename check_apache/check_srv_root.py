#!/usr/bin/env python3

import argparse, sys, os


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
    argumentParser.add_argument(
        "-d", "--dirs", default=["bin", "conf", "logs"],
        help="List of subdirectories whose permissions should be checked")

    return argumentParser.parse_args()

def process_stats(path, verbose=False):
    stats = os.stat(path)

    if verbose:
        print(f"Processing Dir/File: {path}")
        print(f"Stats: {stats}")


def main():
    # Main Plugin Function

    # monitoring plugin return codes
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    if not os.path.isdir(args.path):
        print("CRITICAL: The configured path does not denote a directory!")
        sys.exit(CRITICAL)

    # Process ServerRoot
    process_stats(args.path, args.verbose)

    dirs_to_check = [os.path.join(args.path, dir) for dir in args.dirs]

    if args.verbose:
        print(f"dirs_to_check = {dirs_to_check}")

    for dir in dirs_to_check:
        for root, _, files in os.walk(dir):
            process_stats(root, args.verbose)

            for name in files:
                process_stats(os.path.join(root, name), args.verbose)

    
    sys.exit(OK)


if __name__=="__main__":
	main()