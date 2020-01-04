#!/usr/bin/env python3

import argparse
import sys
import subprocess
import stat
import os
import pwd
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
        help='verbose output'
    )
    argumentParser.add_argument(
        "--tls-ca-cert", default=None,
        help="specify the path to the TLS CA Certificate file (docker CLI option: --tlscacert)"
    )
    argumentParser.add_argument(
        "--tls-cert", default=None,
        help="specify the path to the TLS Server Certificate file (docker CLI option: --tlscert)"
    )
    argumentParser.add_argument(
        "--tls-key", default="/etc/docker/key.json",
        help="specify the path to the TLS Key file (docker CLI option: --tlskey)"
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


def check_file_owner(path: str, owner_group: str) -> bool:
    # parse owner and gorup, format: owner:group
    owner, group = owner_group.split(":")

    # get file stats
    stats = os.stat(path)

    # convert owner and group names to corresponding ids
    user_id = pwd.getpwnam(owner).pw_uid
    group_id = grp.getgrnam(group).gr_gid

    # check user and group
    if stats.st_uid != user_id or stats.st_gid != group_id:
        return False

    return True


def check_file_permissions(path: str, permissions: int) -> bool:
    # get file stats
    stats = os.stat(path)

    # split permissions into owner, group and other
    owner_perm, group_perm, other_perm = [
        int(digit) for digit in str(permissions)]

    # shift owner and gorup permissions to match the masked values from os.stat
    owner_perm <<= 6
    group_perm <<= 3

    # check owner permissions
    if stats.st_mode & stat.S_IRWXU != owner_perm:
        return False

    # check group permissions
    if stats.st_mode & stat.S_IRWXG != group_perm:
        return False

    # check other permissions
    if stats.st_mode & stat.S_IRWXO != other_perm:
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

    # check docker.service file
    if os.path.isfile(docker_srv):

        if not check_file_owner(docker_srv, "root:root"):
            print(
                f"CRITICAL: '{docker_srv}' file owner violation: should be root:root")
            returnCode = CRITICAL

        if not check_file_permissions(docker_srv, 644):
            print(
                f"CRITICAL: '{docker_srv}' file permission violation: should be 644 (rw-r--r--)")
            returnCode = CRITICAL

    # check docker.socket file
    if os.path.isfile(docker_soc):

        if not check_file_owner(docker_soc, "root:root"):
            print(
                f"CRITICAL: '{docker_soc}' owner violation: should be root:root")
            returnCode = CRITICAL

        if not check_file_permissions(docker_soc, 644):
            print(
                f"CRITICAL: '{docker_soc}' permission violation: should be 644 (rw-r--r--)")
            returnCode = CRITICAL

    # check /etc/docker dir
    etc_docker = "/etc/docker"
    if os.path.isdir(etc_docker):

        if not check_file_owner(etc_docker, "root:root"):
            print(
                f"CRITICAL: '{etc_docker}' directory owner violation: should be root:root")
            returnCode = CRITICAL

        if not check_file_permissions(etc_docker, 755):
            print(
                f"CRITICAL: '{etc_docker}' directory permission violation: should be 755 (rwxr-xr-x")
            returnCode = CRITICAL

    # check TLS CA Cert
    if args.tls_ca_cert and os.path.isfile(args.tls_ca_cert):

        if not check_file_owner(args.tls_ca_cert, "root:root"):
            print(
                f"CRITICAL: '{args.tls_ca_cert}' owner violation: should be root:root")
            returnCode = CRITICAL

        if not check_file_permissions(args.tls_ca_cert, 444):
            print(
                f"CRITICAL: '{args.tls_ca_cert}' permission violation: should be 444 (r--r--r--)")
            returnCode = CRITICAL

    # check TLS Cert
    if args.tls_cert and os.path.isfile(args.tls_cert):

        if not check_file_owner(args.tls_cert, "root:root"):
            print(
                f"CRITICAL: '{args.tls_cert}' owner violation: should be root:root")
            returnCode = CRITICAL

        if not check_file_permissions(args.tls_cert, 444):
            print(
                f"CRITICAL: '{args.tls_cert}' permission violation: should be 444 (r--r--r--)")
            returnCode = CRITICAL

    # check TLS key file
    if args.tls_key and os.path.isfile(args.tls_key):

        if not check_file_owner(args.tls_key, "root:root"):
            print(
                f"CRITICAL: '{args.tls_key}' owner violation: should be root:root")
            returnCode = CRITICAL

        if not check_file_permissions(args.tls_key, 400):
            print(
                f"CRITICAL: '{args.tls_key}' permission violation: should be 400 (r--------)")
            returnCode = CRITICAL

    # check /var/run/docker.sock file
    docker_sock = "/var/run/docker.sock"
    if os.path.isfile(docker_sock):

        if not check_file_owner(docker_sock, "root:docker"):
            print(
                f"CRITICAL: '{docker_sock}' owner violation: should be root:docker")
            returnCode = CRITICAL

        if not check_file_permissions(docker_sock, 660):
            print(
                f"CRITICAL: '{docker_sock}' permission violation: should be 660 (rw-rw----)")
            returnCode = CRITICAL

    # check /etc/docker/daemon.json
    docker_daemon = "/etc/docker/daemon.json"
    if os.path.isfile(docker_daemon):

        if not check_file_owner(docker_daemon, "root:root"):
            print(
                f"CRITICAL: '{docker_daemon}' owner violation: should be root:root")
            returnCode = CRITICAL

        if not check_file_permissions(docker_daemon, 644):
            print(
                f"CRITICAL: '{docker_daemon}' permission violation: should be 644 (rw-r--r--)")
            returnCode = CRITICAL

    # check /etc/default/docker
    default_docker = "/etc/default/docker"
    if os.path.isfile(default_docker):

        if not check_file_owner(default_docker, "root:root"):
            print(
                f"CRITICAL: '{default_docker}' owner violation: should be root:root")
            returnCode = CRITICAL

        if not check_file_permissions(default_docker, 644):
            print(
                f"CRITICAL: '{default_docker}' permission violation: should be 644 (rw-r--r--)")
            returnCode = CRITICAL

    # check /etc/sysconfig/docker
    sysconfig_docker = "/etc/sysconfig/docker"
    if os.path.isfile(sysconfig_docker):

        if not check_file_owner(sysconfig_docker, "root:root"):
            print(
                f"CRITICAL: '{sysconfig_docker}' owner violation: should be root:root")
            returnCode = CRITICAL

        if not check_file_permissions(sysconfig_docker, 644):
            print(
                f"CRITICAL: '{sysconfig_docker}' permission violation: should be 644 (rw-r--r--)")
            returnCode = CRITICAL

    if returnCode == OK:
        print(f"OK: docker file permissions set correctly")

    sys.exit(OK)


if __name__ == "__main__":
    main()
