
import os


class FSCheckException(Exception):
    pass


class FSCheck:

    def __init__(self, scan_path="/", store_path="/tmp"):
        self.scan_path = scan_path
        self.store_path = store_path
        self.pid_file_name = "FSCheck.pid"

    def exec(self, output_file_path):
        # check if FSCheck is already running
        if self._is_running():
            # if found: abort
            raise FSCheckException("Process already running!")

        # else: fork process
        pid = os.fork()

        if pid == 0:
            # child process -> execute actual fs check
            self._internal_exec(output_file_path)
        # proc = Process(target=self._internal_exec, args=(self, output_file))
        # proc.start()

    def _is_running(self):
        # check if there's a pid file in the store_path
        return os.path.isfile(os.path.join(self.store_path, self.pid_file_name))

    def _create_pid_file(self):
        with open(os.path.join(self.store_path, self.pid_file_name), "w+") as file:
            file.write(os.getpid())

    def _delete_pid_file(self):
        os.remove(os.path.join(self.store_path, self.pid_file_name))

    def _internal_exec(self, output_file_path):
        # create pid file
        self._create_pid_file()

        # perform actual fs check here

        # delete pid file
        self._delete_pid_file()
