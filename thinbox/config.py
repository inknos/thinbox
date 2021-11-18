import os
import sys
import json
import logging
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
    "THINBOX_HASH_DIR", os.path.join(THINBOX_CACHE_DIR, "hash"))

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
    "THINBOX_CACHE_DIR",
    "THINBOX_CONFIG_DIR",
    "RHEL_BASE_URL",
    "THINBOX_MEMORY",
}

PRIVATE_KEYS = {
    "IMAGE_TAGS",
    "THINBOX_BASE_DIR",
    "THINBOX_IMAGE_DIR",
    "THINBOX_HASH_DIR",
}

KNOWN_KEYS = ALLOWED_KEYS.union(PRIVATE_KEYS)


class Env(dict):
    """Define Thinbox environment

    Env behave like a python dict but it has a restricted set of keys that can contain.
    These keys are defined in by KNOWN_KEYS which is a union of ALLOWED_KEYS and
    PRIVATE_KEYS.

    Each key can be called using python dict style or as a property, although getting
    and setting by property is always preferred.

    Keys are divided into two groups:

    ALLOWED_KEYS can be edited using `thinbox env` command.

    PRIVATE_KEYS can be set editing config files and are supposed to be dangerous or
    private.

    :property THINBOX_CONFIG_DIR: Config dir, defaults to ~/.config/thinbox
    :type THINBOX_CONFIG_DIR: str

    :property THINBOX_CACHE_DIR: Cache dir, defaults to ~/.cache/thinbox
    :type THINBOX_CACHE_DIR: str

    :property THINBOX_BASE_DIR: Base dir, defaults to $THINBOX_CACHE_DIR/base
    :type THINBOX_BASE_DIR: str

    :property THINBOX_IMAGE_DIR: Image dir, defaults to $THINBOX_CACHE_DIR/images
    :type THINBOX_IMAGE_DIR: str

    :property THINBOX_HASH_DIR: Hash dir, defaults to $THINBOX_CACHE_DIR/hash
    :type THINBOX_HASH_DIR: str

    :property THINBOX_MEMORY: Memory size of thinbox domains
    :type THINBOX_MEMORY: int
    """
    def __init__(self, config=None):
        super().__init__()
        # make file optional
        # if file not found write file
        if config:
            self.THINBOX_CONFIG_FILE = config
            self.load()
        else:
            self.THINBOX_CONFIG_DIR = os.path.expanduser('~/.config/thinbox')
            self.THINBOX_CONFIG_FILE = os.path.expanduser('~/.config/thinbox/config.json')

            if not os.path.exists(self.THINBOX_CONFIG_FILE):
                self.load_defaults()
                #self.save()
            else:
                self.load()

        #self.load()
        self._create_cache_dirs()

    def __setitem__(self, key, item):
        #if key not in ALLOWED_KEYS:
        #    print("Cannot set key", key)
        #    sys.exit(1)
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
    def THINBOX_CACHE_DIR(self):
        """Get THINBOX_CACHE_DIR

        :rtype: str
        """
        return os.path.expanduser(self['THINBOX_CACHE_DIR'])

    @THINBOX_CACHE_DIR.setter
    def THINBOX_CACHE_DIR(self, val):
        """Set THINBOX_CACHE_DIR

        :type val: str
        """
        self['THINBOX_CACHE_DIR'] = val

    @property
    def THINBOX_CONFIG_DIR(self):
        """Get THINBOX_CONFIG_DIR

        :rtype: str
        """
        return os.path.expanduser(self['THINBOX_CONFIG_DIR'])

    @THINBOX_CONFIG_DIR.setter
    def THINBOX_CONFIG_DIR(self, val):
        """Set THINBOX_CONFIG_DIR

        :type val: str
        """
        self['THINBOX_CONFIG_DIR'] = val

    @property
    def THINBOX_BASE_DIR(self):
        """Get THINBOX_BASE_DIR

        :rtype: str
        """
        try:
            return os.path.expanduser(self['THINBOX_BASE_DIR'])
        except KeyError:
            self.THINBOX_BASE_DIR = os.path.join(self.THINBOX_CACHE_DIR, 'base')
        return os.path.expanduser(self['THINBOX_BASE_DIR'])

    @THINBOX_BASE_DIR.setter
    def THINBOX_BASE_DIR(self, val):
        """Set THINBOX_BASE_DIR

        :type val: str
        """
        self['THINBOX_BASE_DIR'] = val

    @property
    def THINBOX_IMAGE_DIR(self):
        """Get THINBOX_IMAGE_DIR

        :rtype: str
        """
        try:
            return os.path.expanduser(self['THINBOX_IMAGE_DIR'])
        except KeyError:
            self.THINBOX_IMAGE_DIR = os.path.join(self.THINBOX_CACHE_DIR, 'images')
        return os.path.expanduser(self['THINBOX_IMAGE_DIR'])

    @THINBOX_IMAGE_DIR.setter
    def THINBOX_IMAGE_DIR(self, val):
        """Set THINBOX_IMAGE_DIR

        :type val: str
        """
        self['THINBOX_IMAGE_DIR'] = val

    @property
    def THINBOX_HASH_DIR(self):
        """Get THINBOX_HASH_DIR

        :rtype: str
        """
        try:
            return os.path.expanduser(self['THINBOX_HASH_DIR'])
        except KeyError:
            self.THINBOX_HASH_DIR = os.path.join(self.THINBOX_CACHE_DIR, 'hash')
        return os.path.expanduser(self['THINBOX_HASH_DIR'])

    @THINBOX_HASH_DIR.setter
    def THINBOX_HASH_DIR(self, val):
        """Set THINBOX_HASH_DIR

        :type val: str
        """
        self['THINBOX_HASH_DIR'] = val

    @property
    def RHEL_BASE_URL(self):
        """Get RHEL_BASE_URL

        :rtype: str
        """
        return self.__dict__['RHEL_BASE_URL']

    @property
    def IMAGE_TAGS(self):
        """Get THINBOX_IMAGE_TAGS

        :rtype: str
        """
        return self.__dict__['IMAGE_TAGS']

    @property
    def THINBOX_MEMORY(self):
        """Get THINBOX_MEMORY

        :rtype: int
        """
        return self.__dict__['THINBOX_MEMORY']

    def get_key(self, key):
        """
        """
        return self[key]

    def set_key(self, key, item):
        self[key] = item
        self._create_config_dirs()
        self.save()
        return item

    def _printkv(self, key):
        print(key, "=", self.get_key(key))

    def get(self, key):
        """Get and dump a key to stdout

        :param key: key to dump
        :type key: str
        """
        self._printkv(key)
        return self.get_key(key)

    def set(self, key, item):
        """Set a key and dump it and save config file

        :param key: key to set
        :type key: str

        :param item: item to set
        """
        self.set_key(key, item)
        self._printkv(key)
        return item

    def print(self):
        """Dump object to stdout
        """
        print(json.dumps(self.__dict__, sort_keys=False, indent=4))

    def load(self):
        """Load object from file
        """
        with open(self.THINBOX_CONFIG_FILE) as json_data_file:
            self.__dict__ = json.load(json_data_file)

    def save(self):
        """Save object to file
        """
        if not os.path.exists(self.THINBOX_CONFIG_FILE):
            print("Saved file {}.".format(self.THINBOX_CONFIG_FILE))
        with open(self.THINBOX_CONFIG_FILE, "w") as outfile:
            json.dump(self.__dict__, outfile, indent=4)

    def load_defaults(self):
        """Load and init default values
        """
        self.THINBOX_CACHE_DIR = os.path.expanduser('~/.cache/thinbox')
        self.THINBOX_CONFIG_DIR = os.path.expanduser('~/.config/thinbox')
        self.THINBOX_BASE_DIR = os.path.join(self.THINBOX_CACHE_DIR, 'base')
        self.THINBOX_IMAGE_DIR = os.path.join(self.THINBOX_CACHE_DIR, 'images')
        self.THINBOX_HASH_DIR = os.path.join(self.THINBOX_CACHE_DIR, 'hash')

    def _create_cache_dirs(self):
        self._create_dir(self.THINBOX_CACHE_DIR)
        self._create_dir(self.THINBOX_BASE_DIR)
        self._create_dir(self.THINBOX_IMAGE_DIR)
        self._create_dir(self.THINBOX_HASH_DIR)

    def _create_config_dirs(self):
        self._create_dir(self.THINBOX_CONFIG_DIR)

    def _create_dir(self, name):
        if not os.path.exists(name):
            os.makedirs(name)
            logging.debug("Created dir {}.".format(name))
