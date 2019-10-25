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

    return argumentParser.parse_args()

def process_stats(path, stats):
    pass


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

    # List of directories whose permissions should be checked,
    # args.path denoting the server root
    dirs = ["", "bin", "conf", "logs"].map(lambda x: os.path.join(args.path, x))
    print(dirs)

    raise RuntimeError

    for root, dirs, files in os.walk(args.path):


        if root != args.path and not root in [""]:
            if args.verbose:
                print(f"Skipping directory: {root}")
            continue

        stats = os.stat(root)

        if args.verbose:
            print(f"Processing: {root}")
            print(f"Stats: {stats}")

        process_stats(root, stats)

        for name in files:
            path = os.path.join(root, name)
            stats = os.stat(path)

            if args.verbose:
                print(f"Processing: {path}")
                print(f"Status: {stats}")
            
            process_stats(path, stats)

    
    sys.exit(OK)


if __name__=="__main__":
	main()