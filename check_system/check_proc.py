#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess


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

    return argumentParser.parse_args()


def get_max_pid():
    max_pid_file = "/proc/sys/kernel/pid_max"
    try:
        with open(max_pid_file, "r") as file:
            return int(file.readline())
    except FileNotFoundError:
        print(f"CRITICAL: Could not retrieve max pid from {max_pid_file}")
        sys.exit(CRITICAL)


def parse_ps_output(output):
    # TODO Implement (return set of pids)
    pass


def exec_ps():
    try:
        result = subprocess.check_output("ps -eT", shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"CRITICLA: Failed to execute 'ps -eT' command")
        sys.exit(CRITICAL)
    else:
        return parse_ps_output(result)


# Decorator to check if a ProcessLookupError or
# a FileNotFoundError was thrown
def proc_check(succ):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                func(args, kwargs)
            except ProcessLookupError:
                return PROC_CHECK_NONE
            except FileNotFoundError:
                return PROC_CHECK_NONE
            else:
                return succ

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
    os.lstat(path)


@proc_check(PROC_CHECK_DIR)
def check_dir(path):
    os.listdir(path)


@proc_check(PROC_CHECK_STATVFS)
def check_statvfs(path):
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
            # some tests were successful (maybe not all)
            procs += [(pid, retval)]

    # execute second ps command
    ps2_data = exec_ps()

    # processes that either started or terminated while checks were running
    pid_filter_list = ps_data ^ ps2_data

    report = {}

    for process in procs:
        pid, retval = process

        if not pid in pid_filter_list:
            report[pid] = {
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

    if args.verbose and len(report) > 0:
        print(" | ".join(["PID", "PS1", "PS2", "SIG", "PGID", "SID",
                          "SCHED", "PRIO", "LSTAT", "DIR", "STATVFS"]))

        for pid, rep in report.items():
            print(pid + " | " + " | ".join(rep.values))

    # # calculate set intersection between ps run 1 and run 2
    # # that is: all procs that are in both ps runs (i.e neither started nor terminated)
    # ps_data = ps_data & ps2_data

    # # check if all procs are in ps_data
    # hidden_procs = []
    # for pid in procs:
    #     if not pid in ps_data:
    #         hidden_procs += [pid]

    # if len(hidden_procs) > 0:
    #     print(
    #         f"CRITICAL: found {len(hidden_procs)} hidden processes: {hidden_procs}")
    #     sys.exit(CRITICAL)

    # print("OK: No hidden processes found")
    # sys.exit(OK)


if __name__ == "__main__":
    main()
