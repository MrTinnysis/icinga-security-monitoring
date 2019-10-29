
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

    def get(self, key, vhost=None, default=None):
        value = self.config.get(key, default)

        if vhost:
            vhost_cfg = self.get_vhost_config(vhost)

            if not vhost_cfg:
                print(f"Could not find virtual host config {vhost}")
            else:
                # override value with vhost val if present
                value = vhost_cfg.get(key, value)

        return value

    def get_vhost_config(self, vhost_name):
        vhosts = self.config.get("VirtualHost")

        if not vhosts:
            return None
        elif type(vhosts) == list:
            return next((vh[vhost_name] for vh in vhosts if vhost_name in vh), None)
        else:
            return vhosts.get(vhost_name)

    def reload(self):
        self.config = self._load_cfg()

    def _process_vars(self, value, env_vars):
        if type(value) == str:
            # check if the string contains a placeholder
            match = re.match("\${(\w+?)}", value)
            if match:
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
