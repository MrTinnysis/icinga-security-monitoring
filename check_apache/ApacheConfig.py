
import os
import re

# https://pypi.org/project/apacheconfig/
import apacheconfig


def get_apache_config(path, options=None, env_vars=None, verbose=False):

    if env_vars:
        env_vars = _load_env_vars(env_vars, verbose)


    # set default options if none are given
    options = options if options != None else {
        "useapacheinclude": True,
        "includerelative": True,
        "includedirectories": True,
        "configpath": [os.path.split(path)[0]],
        "flagbits": env_vars,
        #"interpolateenv": env_vars != None,
        "plug": {
            "pre_open": _pre_open_hook
        }
    }

    # print options if verbose output is enabled
    if verbose:
        print(f"options={options}")

    # load config file
    with apacheconfig.make_loader(**options) as loader:
        config = loader.load(path)

    # # load environment variables if provided
    # if env_vars:
    #     env_vars = _load_env_vars(env_vars, verbose)

    #     regex = re.compile("$\{(.*)\}")

    #     for key, val in config.items():
    #         if type(val) != str: continue
    #         match = regex.match(val)
    #         if match:
    #             var = match.group(1)
    #             config[key] = val.replace(f"${{{var}}}", env_vars[var])

    if verbose:
        print(config)

    return config

def _pre_open_hook(file, base):
    print(file)
    return True, file, base

def _load_env_vars(env_vars, verbose=False):
    output = {}
    regex = re.compile("^export (.*)=(.*)$")
    with open(env_vars, "r") as file:
        for line in file:
            match = regex.match(line)

            if match:
                # Suffix currently not supported...
                output[match.group(1)] = match.group(
                    2).replace("$SUFFIX", "")

    if verbose:
        print(output)

    return output
