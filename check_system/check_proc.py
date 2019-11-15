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

# Bitmasks for the different process checks
PROC_CHECK_SIG = 0x01
PROC_CHECK_PGID = 0x02
PROC_CHECK_SID = 0x04
PROC_CHECK_SCHED = 0x08
PROC_CHECK_PRIO = 0x10
PROC_CHECK_LSTAT = 0x20
PROC_CHECK_DIR = 0x40
PROC_CHECK_STATVFS = 0x80
# Bitmask indicating all checks were successful
PROC_CHECK_ALL = 0xff
# Bitmask indicating a failed check
PROC_CHECK_NONE = 0x00


def parse_args():
    # Parses the CLI Arguments and returns a dict containing the
    # corresponding values
    argumentParser = argparse.ArgumentParser()

    argumentParser.add_argument(
        '-v', '--verbose', nargs="?", const=True, default=False,
        help='verbose output'
    )
    argumentParser.add_argument(
        "-r", "--report-type", default="w", choices=["w", "c", "warning", "critical"],
        help=""
    )

    return argumentParser.parse_args()


def pad(string, size, char=" "):
    # pad the given string to the given size using the given char
    while len(string) < size:
        string += char
    return string


def get_max_pid():
    max_pid_file = "/proc/sys/kernel/pid_max"
    try:
        with open(max_pid_file, "r") as file:
            # read max pid from pid_max file
            return int(file.readline())
    except FileNotFoundError:
        print(f"CRITICAL: Could not retrieve max pid from {max_pid_file}")
        sys.exit(CRITICAL)


def parse_ps_output(ps_output):
    output_set = set()
    # regex to match pid from ps -eT output
    regex = re.compile(".*?(?:\d+)\s+(\d+)\s")

    # split output into lines and iterate over lines
    for line in ps_output.split("\n"):
        # match each line
        match = regex.match(line)
        if not match: continue

        # add pid to set -> duplicates are ignored
        pid = int(match.group(1))
        output_set.add(pid)

    return output_set


def exec_ps():
    try:
        # execute ps -eT in a subprocess
        result = subprocess.check_output("ps -eT", shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"CRITICLA: Failed to execute 'ps -eT' command")
        sys.exit(CRITICAL)
    else:
        # parse ps -eT output into a set of pids
        return parse_ps_output(result)


# Decorator to check if a ProcessLookupError or
# a FileNotFoundError was thrown
def proc_check(retval_success):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except ProcessLookupError:
                return PROC_CHECK_NONE
            except FileNotFoundError:
                return PROC_CHECK_NONE
            except PermissionError:
                # Permission Error implies that a process with the given pid exists
                return retval_success
            else:
                return retval_success

        return wrapper
    return decorator


@proc_check(PROC_CHECK_SIG)
def check_sig(pid):
    # try to send a signal to the process
    # yes, in computer science we send signals by calling the
    # function "kill" ¯\_(ツ)_/¯
    # signal "0" indicates to only perform error checking but
    # not actually send anything
    os.kill(pid, 0)


@proc_check(PROC_CHECK_PGID)
def check_pgid(pid):
    # try to retrieve the process group id
    os.getpgid(pid)


@proc_check(PROC_CHECK_SID)
def check_sid(pid):
    # try to retrieve the process' session id
    os.getsid(pid)


@proc_check(PROC_CHECK_SCHED)
def check_sched(pid):
    # try to retrieve scheduling infos
    os.sched_getparam(pid)


@proc_check(PROC_CHECK_PRIO)
def check_prio(pid):
    # try to retrieve scheduling prio
    os.getpriority(os.PRIO_PROCESS, pid)


@proc_check(PROC_CHECK_LSTAT)
def check_lstat(path):
    # try to retrieve folder stats from corresponding /proc dir
    os.lstat(path)


@proc_check(PROC_CHECK_DIR)
def check_dir(path):
    # try to list the corresponding /proc dir
    os.listdir(path)


@proc_check(PROC_CHECK_STATVFS)
def check_statvfs(path):
    # try to retrieve filesystem stats from corresponding /proc dir
    os.statvfs(path)


def check_pid(pid):
    # performs samhain process checks

    # start with empty bitmask
    retval = PROC_CHECK_NONE

    # perform pid checks
    retval |= check_sig(pid)
    retval |= check_pgid(pid)
    retval |= check_sid(pid)
    retval |= check_sched(pid)
    retval |= check_prio(pid)

    # build process path from pid
    path = f"/proc/{pid}"

    # perform path checks (using procfs)
    retval |= check_lstat(path)
    retval |= check_dir(path)
    retval |= check_statvfs(path)

    return retval


def main():
    # Main Plugin Function

    # parse CLI Arguments
    args = parse_args()

    # Print CLI Arguments if verbose output is enabled
    if args.verbose:
        print(args)

    # set min and max pid
    min_pid = 1
    max_pid = get_max_pid()

    # We execute 2 "ps" commands, one before and one after our own checks.
    # This is done to reduce the chance of false positives by detecting
    # processes that started or terminated while the check was running

    # execute first ps command
    ps_data = exec_ps()

    # perform process checks
    procs = []
    # bruteforce entire pid range
    for pid in range(min_pid, max_pid):
        retval = check_pid(pid)
        if retval != PROC_CHECK_NONE:
            # at least one check was successful -> potential process found
            procs += [(pid, retval)]

    # execute second ps command
    ps2_data = exec_ps()

    # Calculate Set-XOR:
    # processes that either started or terminated while checks were running
    pid_filter_list = ps_data ^ ps2_data

    if args.verbose:
        print(f"pid_filter_list={pid_filter_list}")

    # generate reports
    reports = {}
    for process in procs:
        # destructure (pid, retval) tuple
        pid, retval = process

        # check if pid is in filter list (i.e. process started or terminated)
        if not pid in pid_filter_list:
            # create report for given pid
            reports[pid] = {
                "PS1": pid in ps_data,
                "PS2": pid in ps2_data,
                "SIG": retval & PROC_CHECK_SIG != 0,
                "PGID": retval & PROC_CHECK_PGID != 0,
                "SID": retval & PROC_CHECK_SID != 0,
                "SCHED": retval & PROC_CHECK_SCHED != 0,
                "PRIO": retval & PROC_CHECK_PRIO != 0,
                "LSTAT": retval & PROC_CHECK_LSTAT != 0,
                "DIR": retval & PROC_CHECK_DIR != 0,
                "STATVFS": retval & PROC_CHECK_STATVFS != 0
            }

    # print report table
    if args.verbose and len(reports) > 0:
        cols = ["PID", "PS1", "PS2", "SIG", "PGID", "SID", "SCHED", "PRIO", "LSTAT", "DIR", "STATVFS"]
        print(" | ".join([pad(x, 6) for x in cols]))

        for pid, report in reports.items():
            line = pad(str(pid), 6) + " | " + " | ".join([pad(str(val), 6) for val in report.values()])
            print(line)

    misbehaving_procs = []
    # check all reports
    for pid, report in reports.items():
        # if for some reason not all checks were successful
        # report process (pid)
        if not all(report.values()):
            misbehaving_procs += [pid]

    # return corresponding exit code
    if len(misbehaving_procs) > 0:
        if args.report_type in ["w", "warnging"]:
            print(f"WARNING: {len(misbehaving_procs)} misbehaving processes found: {misbehaving_procs}")
            sys.exit(WARNING)
        else:
            print(f"CRITICAL: {len(misbehaving_procs)} misbehaving processes found: {misbehaving_procs}")
            sys.exit(CRITICAL)

    print("OK: No misbehaving processes found")
    sys.exit(OK)


if __name__ == "__main__":
    main()
