
import os
import signal
import stat
import json

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
    def exec(cls, output_file, blacklist=["/proc", "/run", "/sys"], scan_path="/", store_path="/tmp"):
        # create instance
        fs_check = cls(blacklist, scan_path, store_path)

        # check if FSCheck is already running
        if fs_check._is_running():
            #if found: abort
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
            data = {
                "DATE": date.today().isoformat(),
                "SUID": [],
                "SGID": [],
                "WWRT": []
            }

            for root, dirs, files in os.walk(self.scan_path):
                # check blacklisted directories
                for name in dirs:
                    if os.path.join(root, name) in self.blacklist:
                        dirs.remove(name)

                for name in files:
                    self._check_file_stats(os.path.join(root, name), data)

            # create/override output file
            with open(output_file_path, "w+") as file:
                json.dump(data, file, indent=4)

        finally:
            # delete pid file
            self._delete_pid_file()

    def _check_file_stats(self, path, data_out):
        # check if "file" denotes a regular file
        if os.path.islink(path) or not os.path.isfile(path):
            return

        # get file stats (without following links)
        stats = os.stat(path, follow_symlinks=False)

        if stats.st_mode & stat.S_ISUID:
            # regular file with suid flag set
            data_out["SUID"] += [path]

        if stats.st_mode & stat.S_ISGID:
            # regular file with sgid flag set
            data_out["SGID"] += [path]

        if stats.st_mode & stat.S_IWOTH:
            # world writable file
            data_out["WWRT"] += [path]
