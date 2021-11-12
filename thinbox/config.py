import os
import sys
import json
import yaml

from sysconfig import get_config_var

# TODO
# substitute this to avoid deprecation error
# ~/.local/bin/thinbox:14: DeprecationWarning: The distutils package is deprecated and slated for removal in Python 3.12. Use setuptools or check PEP 632 for potential alternatives
#  from distutils.sysconfig import get_python_lib
# ~/.local/bin/thinbox:14: DeprecationWarning: The distutils.sysconfig module is deprecated, use sysconfig instead
#  from distutils.sysconfig import get_python_lib
if sys.version_info <= (3, 10):
    from distutils.sysconfig import get_python_lib
else:
    def get_python_lib(i=0):
        if i == 1:
            return "/usr/lib64/python3.10/site-packages"
        return os.path.join(get_config_var("BINLIBDEST"), "site-packages")

# dbox executable
THINBOX = os.path.basename(sys.argv[0])

# config directory according to XDG
XDG_CONFIG_HOME = os.environ.get(
    "XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
THINBOX_CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "thinbox")
THINBOX_CONFIG_FILE = os.path.join(THINBOX_CONFIG_DIR, "config.json")

# cache directory according to XDG
XDG_CACHE_HOME = os.environ.get(
    "XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
THINBOX_CACHE_DIR = os.path.join(XDG_CACHE_HOME, "thinbox")

# image directory and hashes
THINBOX_BASE_DIR = os.environ.get(
    "THINBOX_BASE_DIR", os.path.join(THINBOX_CACHE_DIR, "base"))
THINBOX_IMAGE_DIR = os.environ.get(
    "THINBOX_IMAGE_DIR", os.path.join(THINBOX_CACHE_DIR, "images"))
THINBOX_HASH_DIR = os.environ.get(
    "THINBOX_HASH_DIR",  os.path.join(THINBOX_CACHE_DIR, "hash"))

# virtual variables
THINBOX_MEMORY = "1024"
THINBOX_SSH_OPTIONS = "-o StrictHostKeyChecking=no -o GlobalKnownHostsFile=/dev/null -o UserKnownHostsFile=/dev/null"

# detect if running in a container
THINBOX_CONTAINER = os.environ.get("THINBOX_CONTAINER", "0") == "1"

# additional variables set inside a container
THINBOX_STACK = os.environ.get("THINBOX_STACK", None)
THINBOX_BASE_IMAGE_NAME = os.environ.get("THINBOX_BASE_IMAGE_NAME", None)
THINBOX_BASE_IMAGE_VERSION = os.environ.get("THINBOX_BASE_IMAGE_VERSION", None)

# environment variables used in the path tweaks
PATHS_ENV = {
    "PYTHON3_SITEARCH": get_python_lib(1),
    "PYTHON3_SITELIB": get_python_lib(),
    "LIBDIR": get_config_var("LIBDIR"),
}

# paths to be used in project path tweaks
PATHS = {
    "CMAKE_MODULE_PATH": ["/usr/share/cmake/Modules"],
    "CMAKE_PREFIX_PATH": ["/usr"],
    "CPATH": ["/usr/include"],
    "LD_LIBRARY_PATH": [PATHS_ENV["LIBDIR"]],
    "LIBRARY_PATH": [PATHS_ENV["LIBDIR"]],
    "PATH": ["/usr/sbin", "/usr/bin"],
    "PKG_CONFIG_PATH": [get_config_var("LIBPC")],
    "PKG_CONFIG_SYSTEM_INCLUDE_PATH": ["/usr/include"],
    "PYTHONPATH": [PATHS_ENV["PYTHON3_SITEARCH"], PATHS_ENV["PYTHON3_SITELIB"]],
}

# RHEL CONFIG
RHEL_BASE_URL = os.environ.get("RHEL_BASE_URL", None)
RHEL_BASE_HASH = {
    "MD5SUM",
    "SHA1SUM",
    "SHA256SUM"
}
RHEL_TAGS = {
    "rhel8-latest"
}

# FEDORA CONFIG
FEDORA_TAGS = {
    "fedora-cloud-34",
    "fedora-cloud-35",
}

FEDORA_IMAGE_URL = {
    "https://mirror.karneval.cz/pub/linux/fedora/linux//releases/$FEDORA_TAGS/Cloud/x86_64/images/",
}

IMAGE_TAGS = []
IMAGE_TAGS.append(list(RHEL_TAGS))
IMAGE_TAGS.append(list(FEDORA_TAGS))
IMAGE_TAGS = IMAGE_TAGS.sort()


ALLOWED_KEYS = {

        "THINBOX_BASE_DIR",
        "THINBOX_IMAGE_DIR",
        "THINBOX_HASH_DIR",
}

PRIVATE_KEYS = {
        "RHEL_BASE_URL",
        "IMAGE_TAGS"
}

KNOWN_KEYS = ALLOWED_KEYS.union(PRIVATE_KEYS)

class Env(dict):
    def __init__(self, config=None):
        super().__init__()
        # make file optional
        # if file not found write file
        if config:
            self._thinbox_config_file = config
        else:
            self._thinbox_config_file = THINBOX_CONFIG_FILE

        self.load()

    def __setitem__(self, key, item):
        if key not in ALLOWED_KEYS:
            print("Cannot set key", key)
            sys.exit(1)
        if key not in KNOWN_KEYS:
            print("Do not know key", key)
            sys.exit(1)

        self.__dict__[key] = item

    def __getitem__(self, key):
        if key not in KNOWN_KEYS:
            print("Do not know key", key)
            sys.exit(1)

        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    @property
    def THINBOX_BASE_DIR(self):
        return os.path.expanduser(self['THINBOX_BASE_DIR'])

    @property
    def THINBOX_IMAGE_DIR(self):
        return os.path.expanduser(self['THINBOX_IMAGE_DIR'])

    @property
    def THINBOX_HASH_DIR(self):
        return os.path.expanduser(self['THINBOX_HASH_DIR'])

    @property
    def RHEL_BASE_URL(self):
        return self.__dict__['RHEL_BASE_URL']

    @property
    def IMAGE_TAGS(self):
        return self.__dict__['IMAGE_TAGS']

    def get(self, key):
        print(key, "=", self[key])

    def set(self, key, item):
        self[key] = item
        print(key, "=", self[key])
        self.save()

    def print(self):
        print(json.dumps(self.__dict__, sort_keys=False, indent=4))

    def load(self):
        with open(self._thinbox_config_file) as json_data_file:
            self.__dict__ = json.load(json_data_file)

    def save(self):
        with open(self._thinbox_config_file, "w") as outfile:
            json.dump(self.__dict__, outfile, indent=4)


