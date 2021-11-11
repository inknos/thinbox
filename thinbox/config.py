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
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "thinbox")
USER_CONFIG = os.path.join(CONFIG_DIR, "config.json")

# cache directory according to XDG
XDG_CACHE_HOME = os.environ.get(
    "XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
CACHE_DIR = os.path.join(XDG_CACHE_HOME, "thinbox")

# image directory and hashes
THINBOX_BASE_DIR = os.environ.get(
    "THINBOX_BASE_DIR", os.path.join(CACHE_DIR, "base"))
THINBOX_IMAGE_DIR = os.environ.get(
    "THINBOX_IMAGE_DIR", os.path.join(CACHE_DIR, "images"))
THINBOX_HASH_DIR = os.environ.get(
    "THINBOX_HASH_DIR",  os.path.join(CACHE_DIR, "hash"))

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


class Env(object):
    def __init__(self, config=None):
        super().__init__()
        # make file optional
        # if file not found write file
        self._thinbox_config_file = USER_CONFIG

        self._thinbox_base_dir = THINBOX_BASE_DIR
        self._thinbox_image_dir = THINBOX_IMAGE_DIR
        self._thinbox_hash_dir = THINBOX_HASH_DIR
        # if dir not found create dir
        self.load()

    @property
    def thinbox_config_file(self):
        return self._thinbox_config_file

    @property
    def thinbox_base_dir(self):
        return self._thinbox_base_dir

    @property
    def thinbox_image_dir(self):
        return self._thinbox_image_dir

    @property
    def thinbox_hash_dir(self):
        return self._thinbox_hash_dir

    def print(self):
        print(json.dumps(self._data, sort_keys=False, indent=4))

    def load(self):
        with open(self.thinbox_config_file) as json_data_file:
            self._data = json.load(json_data_file)

    def save(self):
        with open(self.thinbox_config_file, "w") as outfile:
            json.dump(self._data, outfile)


