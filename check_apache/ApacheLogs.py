
import re
import os
import typing

# https://github.com/rory/apache-log-parser
# https://pypi.org/project/apache-log-parser/1.7.0/
import apache_log_parser

from ApacheConfig import ApacheConfig


class ApacheLogParserException(Exception):
    pass


class ApacheLogParser:

    def __init__(self, config:ApacheConfig, vhost:str=None) -> None:
        log_format_list = config.get("LogFormat", vhost=vhost)
        custom_log = config.get("CustomLog", vhost=vhost)

        # convert format to list if only one format is configured
        if type(log_format_list) != list:
            log_format_list = [log_format_list]

        if not log_format_list:
            raise ApacheLogParserException("No log format specified")

        # CustomLog definition consists of path and either "nickname" or format string
        match = re.match("(.+?) (.+)", custom_log)

        # Check format
        if not match:
            raise ApacheLogParserException(
                f"Invalid CustomLog configuration {custom_log}")

        # set log_file to be the path
        self.log_file = match.group(1)

        # check if nickname/format (format strings are contained in "")
        if match.group(2)[0] == '"' and match.group(2)[-1] == '"':
            # format string (remove "")
            log_format = match.group(2)[1:-1]
        else:
            # nickname
            log_format = self._find_logformat_by_nickname(
                log_format_list, match.group(2))

        if not os.path.isfile(self.log_file):
            raise ApacheLogParserException(
                f"The configured CustomLog path does not denote a file: {self.log_file}")

        # create logfile parser using the given format
        self.parser = apache_log_parser.make_parser(log_format)

    @classmethod
    def from_path(cls, path:str, env:str=None, vhost:str=None):
        config = ApacheConfig(path, env_var_file=env)
        return cls(config, vhost)

    def get_log_data(self, filter_func:function=None, skip_errors:bool=True) -> List[Dict]:
        log_data = []
        with open(self.log_file, "r") as file:
            for line in file:
                try:
                    log_data += [self.parser(line)]
                except apache_log_parser.LineDoesntMatchException as ex:
                    if skip_errors:
                        print("log entry skipped (format missmatch)")
                        continue
                    else:
                        raise ex

        if not filter_func:
            return log_data
        else:
            return [entry for entry in log_data if filter_func(entry)]

    def _find_logformat_by_nickname(self, log_format_list:List[str], nickname:str) -> str:
        regex = re.compile(f'"(.+)" {nickname}$')
        for log_format in log_format_list:
            match = regex.match(log_format)
            if match:
                return match.group(1)

        raise ApacheLogParserException(f"Could not find LogFormat {nickname}")
