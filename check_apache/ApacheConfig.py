
import os
import re

# https://pypi.org/project/apacheconfig/
import apacheconfig


class ApacheConfigException(Exception):
    pass


class ApacheConfig:

    def __init__(self, path, options=None, env_var_file=None):
        self.path = path
        self.env_var_file = env_var_file
        self.options = options if options != None else {
            "useapacheinclude": True,
            "includerelative": True,
            "includedirectories": True,
            "configpath": [os.path.split(path)[0]]
        }

        self.config = self._load_cfg()

        # self.env_vars = None
        # if env_var_file:
        #     self.env_vars = self._parse_env_vars(env_var_file)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def reload(self):
        self.config = self._load_cfg()

    def _process_vars(self, value, env_vars):
        if type(value) == str:
            # check if the string contains a placeholder
            match = re.match("$\{(.+?)\}", value)
            if match:
                print(match)
                try:
                    var = match.group(1)
                    value = value.replace(f"${{{var}}}", env_vars[var])
                except KeyError:
                    raise ApacheConfigException(
                        f"Undefined variable ${{{var}}}")

        elif type(value) == dict:
            # iterate dict
            for key, val in value.items():
                # process each value separately and update dict
                value[key] = self._process_vars(val, env_vars)

        else:
            # assume generic iterable (list)
            value = [self._process_vars(val, env_vars) for val in value]

        return value

    def _load_cfg(self):
        with apacheconfig.make_loader(**self.options) as loader:
            config = loader.load(self.path)

        if self.env_var_file:
            env_vars = self._parse_env_vars()
            print(f"env_vars={env_vars}")
            for key, value in config.items():
                config[key] = self._process_vars(value, env_vars)

        return config

    def _parse_env_vars(self):
        env_vars = {}
        regex = re.compile("^export (.*)=(.*)$")
        with open(self.env_var_file, "r") as file:
            for line in file:
                match = regex.match(line)

                if match:
                    # Suffix currently not supported...
                    env_vars[match.group(1)] = match.group(
                        2).replace("$SUFFIX", "")

        return env_vars

    def __repr__(self):
        return self.config.__repr__()


# def get_apache_config(path, options=None, env_vars=None, verbose=False):

#     # if env_vars:
#     #     env_vars = _load_env_vars(env_vars, verbose)

#     # set default options if none are given
#     options = options if options != None else {
#         "useapacheinclude": True,
#         "includerelative": True,
#         "includedirectories": True,
#         "configpath": [os.path.split(path)[0]]
#     }

#     # load config file
#     with apacheconfig.make_loader(**options) as loader:
#         config = loader.load(path)

#     # load environment variables if provided
#     if env_vars:
#         env_vars = _load_env_vars(env_vars, verbose)

#         #regex = re.compile("$\{(.+?)\}")

#         for key, value in config.items():
#             if type(value) == str:
#                 match = re.match("$\{(.+?)\}", value)

#                 if match:
#                     var = match.group(1)


#             if type(value) != str:
#                 continue
#             match = regex.match(value)
#             if match:
#                 var = match.group(1)
#                 config[key] = value.replace(f"${{{var}}}", env_vars[var])

#     if verbose:
#         print(config)

#     return config


# def _load_env_vars(env_vars, verbose=False):
#     output = {}
#     regex = re.compile("^export (.*)=(.*)$")
#     with open(env_vars, "r") as file:
#         for line in file:
#             match = regex.match(line)

#             if match:
#                 # Suffix currently not supported...
#                 output[match.group(1)] = match.group(
#                     2).replace("$SUFFIX", "")

#     if verbose:
#         print(output)

#     return output
