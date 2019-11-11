
import os
import signal
import stat

from datetime import date


class FSCheckException(Exception):
    pass


class FSCheck:

    def __init__(self, blacklist, scan_path, store_path):
        self.blacklist = blacklist
        self.scan_path = scan_path
        self.store_path = store_path
        self.pid_file_name = "FSCheck.pid"
        # make sure pid file gets deleted if process is killed
        signal.signal(signal.SIGINT, self._delete_pid_file)
        signal.signal(signal.SIGTERM, self._delete_pid_file)

    @classmethod
    def exec(cls, output_file, blacklist=None, scan_path="/", store_path="/tmp"):
        if not blacklist:
            blacklist = ["/proc", "/run", "/sys", "/snap", "/var/lib/lxcfs"]

        # create instance
        fs_check = cls(blacklist, scan_path, store_path)

        # check if FSCheck is already running
        if fs_check._is_running():
            #if found: aboort
            raise FSCheckException("Process already running!")

        # else: fork process
        pid = os.fork()

        if pid == 0:
            # child process -> execute actual fs check
            fs_check._internal_exec(output_file)

    def _is_running(self):
        # check if there's a pid file in the store_path
        return os.path.exists(os.path.join(self.store_path, self.pid_file_name))

    def _create_pid_file(self):
        with open(os.path.join(self.store_path, self.pid_file_name), "w+") as file:
            file.write(str(os.getpid()))

    def _delete_pid_file(self):
        os.remove(os.path.join(self.store_path, self.pid_file_name))

    def _internal_exec(self, output_file_path):
        # create pid file
        self._create_pid_file()

        # perform actual fs check here
        try:
            # add current iso date as first line
            data = [date.today().isoformat()]

            for root, dirs, files in os.walk(self.scan_path):
                # check blacklisted directories
                for name in dirs:
                    if os.path.join(root, name) in self.blacklist:
                        dirs.remove(name)

                for name in files:
                    data += self._check_file_stats(
                        os.path.join(root, name))

            # create/override output file
            with open(output_file_path, "w+") as file:
                for line in data:
                    file.write(line + "\n")
        finally:
            # delete pid file
            self._delete_pid_file()

    def _check_file_stats(self, file):
        # check if file is indeed a file (and not a link or anything else)
        if not os.path.isfile(file):
            return []

        stats = os.stat(file)
        data = []

        if stats.st_mode & stat.S_ISUID:
            # SUID Flag set
            data += ["SUID:" + file]

        if stats.st_mode & stat.S_ISGID:
            # SGID Flag set
            data += ["SGID:" + file]

        if stats.st_mode & stat.S_IWOTH:
            # world writable file
            data += ["WWRT:" + file]

        return data
