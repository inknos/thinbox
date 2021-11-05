#!/usr/bin/python3.10
# PYTHON_ARGCOMPLETE_OK

import argparse
import hashlib
import logging
import os
import re
import requests
import shutil
import subprocess
import sys

from time import sleep
from argcomplete.completers import ChoicesCompleter
from paramiko import SSHClient
from scp import SCPClient
from sysconfig import get_config_var
from urllib.parse import urlparse

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


try:
    import argcomplete
    USE_ARGCOMPLETE = True
except ImportError:
    USE_ARGCOMPLETE = False


# dbox executable
THINBOX = os.path.basename(sys.argv[0])

# config directory according to XDG
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "thinbox")
USER_CONFIG = os.path.join(CONFIG_DIR, "user.thinbox.yaml")

# cache directory according to XDG
XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
CACHE_DIR = os.path.join(XDG_CACHE_HOME, "thinbox")

# image directory and hashes
THINBOX_BASE_DIR = os.environ.get("THINBOX_BASE_DIR", os.path.join(CACHE_DIR, "base"))
THINBOX_IMAGE_DIR = os.environ.get("THINBOX_IMAGE_DIR", os.path.join(CACHE_DIR, "images"))
THINBOX_HASH_DIR  = os.environ.get("THINBOX_HASH_DIR",  os.path.join(CACHE_DIR, "hash"))

# virtual variables
THINBOX_MEMORY="1024"
THINBOX_SSH_OPTIONS="-o StrictHostKeyChecking=no -o GlobalKnownHostsFile=/dev/null -o UserKnownHostsFile=/dev/null"

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

RHEL_IMAGE_HASH = {
    "MD5SUM",
    "SHA1SUM",
    "SHA256SUM"
}
RHEL_IMAGE_DOMAIN = {
    "download-node-02.eng.bos.redhat.com",
    "redhat.com"
}

def _url_is_valid(url):
    """Validate a url format based on Django validator

    The validation is done through regex and it was taken from:
    https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
    https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45

    Parameters
    ----------
    url : str
        The url to validate

    Returns
    -------
    bool
        True if the url is valid
    """

    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def _ping_url(url):
    """Ping a url to see if site is available

    Example from:
    https://stackoverflow.com/questions/316866/ping-a-site-in-python

    Parameters
    ----------
    url : str
        The url to ping

    Returns
    -------
    bool
        True if the ping has 0% packet loss
    """
    ping_response = subprocess.Popen(
        ["ping", "-c3", url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    ping_stdout.stdout.read()
    ping_stderr.stderr.read()
    if ping_stderr != b'':
        logger.error("Ping error: {}".format(ping_stderr.decode('utf8')))
        sys.exit(1)
    result = ping_stdout.decode('utf-8')
    return "0% packet loss" in result

def is_virt_enabled():
    env = os.environ.copy()
    env["LC_LANG"] = "C"
    out = subprocess.run(["lscpu"], env=env, stdout=subprocess.PIPE)
    return "VT-x" in str(out.stdout)

class Thinbox(object):
    """
    A class made to represent a Thinbox run

    Attributes
    ----------
    all_machines : list
        list of names of all machines

    all_running_machines : list
        list of names of all running machines

    all_stopped_machines : list
        list of names of all stopped machines

    all_paused_machines : list
        list of names of all paused machines

    all_other_machines : list
        list of names of all other machines

    Methods
    -------
    pull(tag=None, url=None)
        Pulls a base image from a url or from a tag

    enter(name)
        Enter machine
    """
    def __init__(self):
        super().__init__()
        self._all_machines = self._get_all_machines()
        self._all_running_machines = self._get_all_running_machines()
        self._all_stopped_machines = self._get_all_stopped_machines()
        self._all_paused_machines  = self._get_all_paused_machines()
        self._all_other_machines   = self._get_all_other_machines()

    @property
    def all_machines(self):
        return self._all_machines

    @property
    def all_running_machines(self):
        return self._all_running_machines

    @property
    def all_stopped_machines(self):
        return self._all_stopped_machines

    @property
    def all_paused_machines(self):
        return self._all_paused_machines

    @property
    def all_other_machines(self):
        return self._all_other_machines

    def _detect_os_from_url(self, url):
        return None
        if url is None:
            return None
        domain = urlparse(url).netloc
        if domain in RHEL_IMAGE_DOMAIN:
            return "rhel"
        if domain in FEDORA_IMAGE_DOMAIN:
            return "fedora"

    def stop(self, name, opt=None):
        """Stop running machine

        Parameters
        ----------
        name : str
            Name of machine to stop

        opt : str, optional
            Options to pass to virsh command
            Options are None, "--mode=acpi"
        """
        if not _machine_exists(name):
            print("Machine '{}' does not exist".format(name))
            sys.exit(1)
        if not _machine_is_running(name):
            print("Machine '{}' already stopped.".format(name))
            return
        command = ['virsh', 'shutdown']
        if opt == "--mode=acpi":
            command.append(opt)
        command.append(name)
        p_shutdown = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Machine '{}' is being shutdown.".format(name))
        _logging_subprocess(p_shutdown, "virsh shutdown: {}")

    def start(self, name):
        """Start a machine

        Parameters
        ----------

        name : str
            Name of machine to start
        """
        if not _machine_exists(name):
            print("Machine '{}' does not exist".format(name))
            sys.exit(1)
        if _machine_is_running(name):
            print("Machine '{}' is already running.".format(name))
            print("To SSH in it run: thinbox enter {}".format(name))
            return
        self._start_machine(name)
        print("Machine '{}' started.".format(name))
        print("To SSH in it run: thinbox enter {}".format(name))

    def remove(self, name):
        """Remove a machine of given name

        Parameters
        ---------
        name : str
            Name of machine to remove
        """
        # check if machine exists
        if not _machine_exists(name):
            logging.error("Machine with name '{}' does not exist.".format(name))
            sys.exit(1)

        # stop the machine
        p_destroy = subprocess.Popen(
            ['virsh', 'destroy', name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _logging_subprocess(p_destroy, "virsh destroy: {}")
        p_undefine = subprocess.Popen(
            ['virsh', 'undefine', name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _logging_subprocess(p_undefine, "virsh undefine: {}")

        # check if file exists
        filepath = os.path.join(THINBOX_IMAGE_DIR, name + ".qcow2")
        if os.path.exists(filepath):
            os.remove(filepath)
        else:
            logging.warning("File does not exist: {}".format(filepath))

    def remove_all(self):
        """Remove all machines found with self._get_all_machines
        """
        machines = self._get_all_machines()
        for m in machines:
            self.remove(m)

    def pull(self, tag=None, url=None):
        """Download a qcow2 image file from tag or url

        Parameters
        ----------
        tag : str
            Tag of image to download (RHEL only)

        url : str
            Url of image to download
        """

        if tag:
            print("tag is", tag)

        if url:
            download_image(url)

    def image(self):
        """Print a list of base images on the system
        """
        self.image_list()

    def image_list(self):
        """Print a list of base images on the system
        """
        _image_list()

    def copy(self, files, name, directory="/root", pre="", command=""):
        """Copy file or files into a running machine

        Parameters
        ----------
        files : list
            List of files to copy in the machine

        name : str
            Name of machine to copy file/files in

        command :  str, optional
            Command to run inside the machine after files are copied

        directory : str, optional
            Destination directory for files to be copied in. (default is "/root")

        pre : str, optional
            Command to run inside the machine before the files are copied
        """
        # machine exist?
        if not _machine_exists(name):
            logging.error("Machine with name '{}' does not exist.".format(name))
            sys.exit(1)
        # TODO
        # is machine running?
        # do you want to start it?
        # get ip
        ip = _get_ip(name)

        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.connect(hostname=ip, username="root")

        # run command
        if pre:
            _run_ssh_command(ssh, pre)

        # copy file
        if directory:
            destination = directory
        else:
            destination = "/root"
        with SCPClient(ssh.get_transport()) as scp:
            for file in files:
                dest = os.path.join(destination, os.path.basename(file))
                scp.put(file, dest)
                print("Copied file {} into {}.".format(file, dest))

        # run post
        if command:
            _run_ssh_command(ssh, command)


    def list(self, fil=""):
        """List machines

        Parameters
        ----------
        fil : str, optional
            Filter machines by state
            Options are "", "running", "stopped", "paused", "other"
        """
        running = []
        stopped = []
        other   = []
        paused  = []
        if fil == "":
            running = self._get_all_running_machines()
            stopped = self._get_all_stopped_machines()
            paused  = self._get_all_stopped_machines()
            other   = self._get_all_other_machines()
            print(len(running + stopped + other + paused), "machines.")
        elif fil == "other":
            other = self._get_all_other_machines()
            print(len(other), fil, "machines")
        elif fil == "paused":
            paused = self._get_all_paused_machines()
            print(len(paused), fil, "machines")
        elif fil == "running":
            running = self._get_all_running_machines()
            print(len(running), fil, "machines")
        elif fil == "stopped":
            stopped = self._get_all_stopped_machines()
            print(len(stopped), fil, "machines")

        if len(running + stopped + paused + other) == 0:
            print("To create a machine run: thinbox create -i <image> <name>")
            return
        print_format = "{:<20} {:<8} {:<16} {:<10}"
        print(print_format.format("MACHINE", "STATE", "IP", "MAC"))
        if running != []:
            for m in running:
                print(print_format.format(m,"running", _get_ip(m), _get_mac(m)))
        if stopped != []:
            for m in stopped:
                print(print_format.format(m,"stopped", _get_ip(m), _get_mac(m)))
        if paused != []:
            for m in paused:
                print(print_format.format(m,"paused", _get_ip(m), _get_mac(m)))
        if other != []:
            for m in other:
                print(print_format.format(m,"other", _get_ip(m), _get_mac(m)))

    def image_rm(self):
        pass

    def enter(self, name):
        """Enter machine via ssh

        If machine is stopped, start it

        Parameters
        ----------
        name : str
            Name of machine to ssh into
        """
        # if machine is not up, start it
        if name in self._get_all_stopped_machines():
            self._start_machine(name)
        self._wait_for_boot(name)
        _get_ip(name)
        _ssh_connect(name)

    def create(self):
        print("create")

    def create_from_image(self, base_name, name):

        if not os.path.exists(THINBOX_IMAGE_DIR):
            os.makedirs(THINBOX_IMAGE_DIR)
        image = os.path.join(THINBOX_IMAGE_DIR, name + ".qcow2")
        base = os.path.join(THINBOX_BASE_DIR, base_name)
        if not os.path.exists(base):
            logging.error("Image {} not found in {}.".format(base, THINBOX_BASE_DIR))
            if not _image_name_wrong(base):
                print("Maybe the filename is incorrect?")
            print("To list the available images run: thinbox image")
            sys.exit(1)

        # ensure_domain_undefined $name

        if _machine_exists(name):
            logging.error("Machine with name '{}' exists.".format(name))
            sys.exit(1)

        p_qemu = subprocess.Popen([
            'qemu-img', 'create',
            '-f', 'qcow2', '-o',
            'backing_file='+ base +',backing_fmt=qcow2', image],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _logging_subprocess(p_qemu, "qemu: {}")

        p_virt_sysprep = subprocess.Popen([
            'virt-sysprep', '-a', image,
            '--hostname', name, '--ssh-inject', 'root',
            '--selinux-relabel'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _logging_subprocess(p_virt_sysprep, "virt-sysprep: {}")

        p_virt_install = subprocess.Popen([
            'virt-install', '--network=bridge:virbr0',
            '--name', name, '--memory', THINBOX_MEMORY,
            '--disk', image,
            '--import',
            '--os-type=linux',
            '--os-variant=none',
            '--noautoconsole'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _logging_subprocess(p_virt_install, "virt-install: {}")


    def _wait_for_boot(self, name):
        ip = _get_ip(name)
        import itertools, sys
        spinner = itertools.cycle(['-', '/', '|', '\\'])
        print("Machine '{}' is starting. ".format(name), sep="", end="")
        while ip == "":
            sys.stdout.write(next(spinner))   # write the next character
            sys.stdout.flush()                # flush stdout buffer (actual character display)
            sys.stdout.write('\b')            # erase the last written char
            sleep(0.5)
            ip = _get_ip(name)
        print()

    def _start_machine(self, name):
        p_start = subprocess.Popen(
            ['virsh', 'start', name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _logging_subprocess(p_start, "virsh start: {}")

    def _get_all_machines(self, state="--all"):
        p_virsh = subprocess.Popen(
            ['virsh', 'list', '--name', state],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out = p_virsh.stdout.read().decode('utf8').strip().split('\n')
        return list(filter(None, out))

    def _get_all_running_machines(self):
        return self._get_all_machines('--state-running')

    def _get_all_stopped_machines(self):
        return self._get_all_machines('--state-shutoff')

    def _get_all_paused_machines(self):
        return self._get_all_machines('--state-paused')

    def _get_all_other_machines(self):
        return self._get_all_machines('--state-other')


def _run_ssh_command(session, cmd):
    print("Command", cmd)

    ssh_stdin, ssh_stdout, ssh_stderr = session.exec_command(cmd)
    exit_code = ssh_stdout.channel.recv_exit_status() # handles async exit error

    for line in ssh_stdout:
        print(line.strip())

    if exit_code != 0:
        logging.warning("paramiko error: {}".format(exit_code))
        for line in ssh_stderr:
            logging.warning("paramiko stderr: {}".format(line.strip()))


def _machine_exists(name):
    """Returns True if VM name refers to an existing machine

    Run virh list --name --all and check output

    Parameters
    ----------
    name : string
        Machine name to check

    Returns
    -------
    bool
        True if machine of given name exist
    """
    p_list = subprocess.Popen(
        ['virsh', 'list', '--name', '--all'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return name in p_list.stdout.read().decode('utf8').strip().split('\n')

def _image_name_wrong(name):
    return name.endswith(".qcow2")

def _machine_is_running(name):
    """Returns True if VM name refers to an existing and running machine

    Run virh list --name and check output

    Parameters
    ----------
    name : string
        Machine name to check

    Returns
    -------
    bool
        True if machine of given name exists and is running
    """
    p_list = subprocess.Popen(
        ['virsh', 'list', '--name'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return _machine_exists(name) and name in p_list.stdout.read().decode('utf8').strip().split('\n')

def _logging_subprocess(process, output):
    for so in process.stdout.read().decode('utf8').split('\n'):
        if so == '':
            continue
        logging.debug(output.format(so))
    for se in process.stderr.read().decode('utf8').split('\n'):
        if se == '':
            continue
        logging.error(output.format(se))

def _get_mac(name):
    """Gets MAC of machine

    Parameters
    ----------
    name : str
        Name of machine to query IP of

    Returns
    -------
    str
        MAC of machine
    """
    p_virsh = subprocess.Popen(['virsh', 'domiflist', name],
            stdout=subprocess.PIPE)
    mac = p_virsh.stdout.read().decode('utf8')
    logging.debug("mac: {}".format(mac))
    return mac.strip()[-17:]

def _get_ip(name):
    """Gets ip from arp table

    Parameters
    ----------
    name : str
        Name of machine to query for IP

    Returns
    -------
    str
        IP of machine
    """
    mac = _get_mac(name)
    ip = ""
    with open("/proc/net/arp", "r") as arp:
        for line in arp:
            if mac in line:
                ip = line
                break
    #p_arp = subprocess.Popen(['arp', '-na'], stdout=subprocess.PIPE)
    #out = p_arp.stdout.read().decode('utf8')
    #ip = [ ip for ip in out.strip().split('\n') if mac in ip ][0]
    if ip == "":
        return ip
    ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', ip )[0]
    logging.debug("Ip: {}".format(ip))
    return ip

def _ssh_connect(name):
    mac = _get_mac(name)
    ip = _get_ip(name)
    logging.debug("options: {}".format(THINBOX_SSH_OPTIONS))
    os.system("ssh {} root@{}".format(THINBOX_SSH_OPTIONS, ip))

def _image_list():
    image_list = []
    for root, dirs, files in os.walk(THINBOX_BASE_DIR):
        for file in files:
            image_list.append(file)
    print(THINBOX_BASE_DIR)
    print()
    print("{:<50} {:<20}".format("IMAGE", "HASH"))
    for name in image_list:
        print("{:<50} ".format(name), end="")
        none = True
        hashes = []
        for hashfunc in sorted(RHEL_IMAGE_HASH):
            if os.path.exists(os.path.join(THINBOX_HASH_DIR, name + "." + hashfunc + ".OK")):
                hashes.append(hashfunc)
                none = False
        if none:
            print("NONE", end="")
        else:
            print(",".join(hashes), end="")

        print()

def download_image(url):
    filename = os.path.split(url)[-1]
    filepath = os.path.join(THINBOX_BASE_DIR, filename)
    # check dir exist
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    _download_file(url, filepath)
    #TODO download hash
    # this works for rhel
    if urlparse(url).netloc in RHEL_IMAGE_DOMAIN:
        print("HASH")
        hashpath = os.path.join(THINBOX_HASH_DIR, filename)
        for ext in RHEL_IMAGE_HASH:
            _download_file(url + "." + ext, hashpath + "." + ext)
    if check_hash(filename, "sha256"):
        print("Image downloaded, verified, and ready to use")
    else:
        print("Image downloaded and ready to use but not verified.")

def check_hash(filename, hashname="md5"):
    if hashname == "md5" or hashname == "md5sum":
        hashfunc = hashlib.md5()
        ext = "MD5SUM"
    elif hashname == "sha1" or hashname == "sha1sum":
        hashfunc = hashlib.sha1()
        ext = "SHA1SUM"
    elif hashname == "sha256" or hashname == "sha256sum":
        hashfunc = hashlib.sha256()
        ext = "SHA256SUM"
    else:
        logger.error("Not a valid hash function: {}".format(hashname))
    result, hh, hf = _check_hash(filename, ext, hashfunc)

    logging.debug("File hash is {}.".format(hf))
    logging.debug("Expected {} is {}.".format(hashname, hh))
    if not result:
        logging.info("Continue withouth hash verification")
        return result
    if not hh == hf:
        logging.error("Hashes do not match")
        sys.exit(1)

    return result

def _check_hash(filename, ext, hashfunc):
    """"This function returns the SHA-1 hash
    of the file passed into it"""
    h = hashfunc
    filepath = os.path.join(THINBOX_BASE_DIR, filename)
    hashpath = os.path.join(THINBOX_HASH_DIR, filename + "." + ext)
    if not os.path.exists(filepath):
        logging.error("Image file {} does not exists.".format(filepath))
        if not _image_name_wrong(filepath):
            print("Maybe the filename is incorrect?")
        print("To list the available images run: thinbox image")
        sys.exit(1)
    if not os.path.exists(hashpath):
        logging.warning("Hash file {} does not exists.".format(filepath))
        return False, "", ""
    # if hash/imagename.hash.OK exists return True
    if os.path.exists(hashpath + ".OK"):
        with open(hashpath + ".OK", 'r') as file:
            file.readline()
            last = file.readline()
        hf = last.strip().split(' ')[-1]
        print("Found file that verifies a previous hash check for {}".format(ext))
        return True, hf, hf

    with open(hashpath, 'r') as file:
        file.readline()
        last = file.readline()
    with open(filepath,'rb') as file:
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            h.update(chunk)
    hh = h.hexdigest()
    hf = last.strip().split(' ')[-1]

    # if hash is good create hash/imagename.hash.OK
    if hh == hf:
        shutil.copyfile(hashpath, hashpath + ".OK")
    return hh == hf, hh, hf


def _download_file(url, filepath):
    """Download file from url to specific path

    Parameters
    ----------
    url : str
        Location of file to be downloaded

    path : str
        Path where the file will be saved

    Returns
    -------
    bool
        True if file is successfully downloaded
    """
    _url_is_valid(url)

    # check file exist
    if os.path.exists(filepath):
        logging.debug("File {} exists.".format(filepath))
        return False
    with open(filepath, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')
    return True

def get_parser():
    """
    Returns a parser with this structure
    thinbox create
               |
               +-- -i/--image <image> <vm_name>
               +-- -p/--path  <path>  <vm_name>
               +-- -t/--tag   <image> <vm_name>
               +-- -u/--url   <url>   <vm_name>

    thinbox pull
             |
             +-- -t/--tag <tag>
             +-- -u/--url <url>

    thinbox image
              |
              +-- list/ls
              +-- remove/rm <image>
                        |
                        +-- -a

    thinbox copy <files> <vm_name>
             |
             +-- -c/--command   <command to exec before>
             +-- -d/--dir       <destination dir>
             +-- -p/--pre       <command to exec after>

    thinbox
        |
        +-- list/ls -----------------|
        |       |                    |
        |       +-- -a/--all         |
        |       +-- -o/--other       |
        |       +-- -p/--paused      |
        |       +-- -r/--running     |
        |       +-- -s/--stopped     |
        +-- remove/rm <vm_name> --------|
                  |                  |  |
                  +-- -a ------------------|
                                     |  |  |
    thinbox vm                       |  |  |
           |                         |  |  |
           +-- list/ls --------------|  |  |
           |    +-- -a/--all            |  |
           |    +-- -o/--other          |  |
           |    +-- -p/--paused         |  |
           |    +-- -r/--running        |  |
           |    +-- -s/--stopped        |  |
           +-- remove/rm <vm_name> -----|  |
                     |                     |
                     +-- -a ---------------|

    thinbox enter <vm_name>
    thinbox start <vm_name>
    thinbox stop  <vm_name>
    """

    tb = Thinbox()

    parser = argparse.ArgumentParser(#usage="%(prog)s <command> [opts] [args]",
        description="Thinbox is a tool for..",
        formatter_class=Formatter,
    )
    parser.add_argument(
            "-v",
            "--verbose",
            help="increase output verbosity",
            action="store_true"
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
    )

    pull_parser = subparsers.add_parser(
        "pull",
        help="pull base image from TAG or URL"
    )
    pull_parser_mg = pull_parser.add_mutually_exclusive_group(required=True)
    pull_parser_mg.add_argument(
        "-t", "--tag",
        help="TAG of the image you want to pull"
    )
    pull_parser_mg.add_argument(
        "-u", "--url",
        help="URL of the image you want to pull"
    )

    # create
    create_parser = subparsers.add_parser(
        "create",
        help="create VM from base image",
    )
    create_parser.add_argument(
        "name",
        help="name of the VM"
    )
    create_parser_mg = create_parser.add_mutually_exclusive_group(required=True)
    create_parser_mg.add_argument(
        "-i", "--image",
        help="Name of image already downloaded"
    )
    create_parser_mg.add_argument(
        "-p", "--path",
        help="Path of image you want to create a vm from"
    )
    create_parser_mg.add_argument(
        "-t", "--tag",
        help="TAG of the image you want to pull"
    )
    create_parser_mg.add_argument(
        "-u", "--url",
        help="URL of the image you want to pull"
    )
    # copy
    copy_parser = subparsers.add_parser(
        "copy",
        aliases = ["cp"],
        help="copy files into specified VM"
    )
    copy_parser.add_argument(
        "file",
        nargs="+",
        help="file or files to copy"
    )
    copy_parser.add_argument(
        "name",
        help="name of the VM"
    )
    copy_parser_mg = copy_parser.add_argument_group()
    copy_parser_mg.add_argument(
        "-c",
        "--comm",
        help="command to execute after the copy"
    )
    copy_parser_mg.add_argument(
        "-d",
        "--dir",
        help="destination dirpath of copy"
    )
    copy_parser_mg.add_argument(
        "-p",
        "--pre",
        help="command to execute before the copy"
    )

    # list
    list_parser = subparsers.add_parser(
        "list",
        aliases = ['ls'],
        help="list available VMs"
    )
    list_parser_mg = list_parser.add_mutually_exclusive_group(required=False)
    list_parser_mg.add_argument(
        "-a", "--all",
        action="store_const",
        const=True,
        help="List all VMs"
    )
    list_parser_mg.add_argument(
        "-o", "--other",
        action="store_const",
        const=True,
        help="List all other VMs"
    )
    list_parser_mg.add_argument(
        "-p", "--paused",
        action="store_const",
        const=True,
        help="List all paused VMs"
    )
    list_parser_mg.add_argument(
        "-r", "--running",
        action="store_const",
        const=True,
        help="List all running VMs"
    )
    list_parser_mg.add_argument(
        "-s", "--stopped",
        action="store_const",
        const=True,
        help="List all stopped VMs"
    )
    # remove
    remove_parser = subparsers.add_parser(
        "remove",
        aliases = ['rm'],
        help="remove VM"
    )
    remove_parser_mg = remove_parser.add_mutually_exclusive_group(required=True)
    remove_parser_mg.add_argument(
        "-a", "--all",
        action='store_const',
        const=True,
        help="Remove all VMs"
    )
    remove_parser_mg.add_argument(
        "name",
        nargs="?",
        help="Remove a VM of name"
    )
    # image
    image_parser = subparsers.add_parser(
        "image",
        aliases = ['img'],
        help="manage base images"
    )
    # vm
    vm_parser = subparsers.add_parser(
        "vm",
        help="manage VMs"
    )
    vm_subparser = vm_parser.add_subparsers(
        dest="vm_parser"
    )
    vm_list_parser = vm_subparser.add_parser(
        "list",
        aliases=["ls"],
        help="VM list "
    )
    vm_list_parser_mg = vm_list_parser.add_mutually_exclusive_group(required=False)
    vm_list_parser_mg.add_argument(
        "-a", "--all",
        action="store_const",
        const=True,
        help="List all VMs"
    )
    vm_list_parser_mg.add_argument(
        "-o", "--other",
        action="store_const",
        const=True,
        help="List all other VMs"
    )
    vm_list_parser_mg.add_argument(
        "-p", "--paused",
        action="store_const",
        const=True,
        help="List all paused VMs"
    )
    vm_list_parser_mg.add_argument(
        "-r", "--running",
        action="store_const",
        const=True,
        help="List all running VMs"
    )
    vm_list_parser_mg.add_argument(
        "-s", "--stopped",
        action="store_const",
        const=True,
        help="List all stopped VMs"
    )
    vm_remove_parser = vm_subparser.add_parser(
        "remove",
        aliases=['rm'],
        help="remove VM"
    )
    vm_remove_parser_mg = vm_remove_parser.add_mutually_exclusive_group(required=True)
    vm_remove_parser_mg.add_argument(
        "-a", "--all",
        action='store_const',
        const=True,
        help="Remove all VMs"
    )
    vm_remove_parser_mg.add_argument(
        "name",
        nargs="?",
        help="Remove a VM of name"
    )
    # enter
    enter_parser = subparsers.add_parser(
        "enter",
        help="enter VM"
    )
    enter_parser.add_argument(
        "name",
        help="name of the VM to enter",
        choices=tb.all_machines
    )
    # start
    start_parser = subparsers.add_parser(
        "start",
        help="start VM"
    )
    start_parser.add_argument(
        "name",
        choices=tb.all_stopped_machines,
        help="name of the VM to start"
    )
    # stop
    stop_parser = subparsers.add_parser(
        "stop",
        help="stop VM"
    )
    stop_parser.add_argument(
        "name",
        choices=tb.all_running_machines,
        help="name of the VM to stop"
    )
    stop_parser_mg = stop_parser.add_mutually_exclusive_group(required=False)
    stop_parser_mg.add_argument(
        "-f", "--force",
        help="Force shuotdown of machine with sending ACPI"
    )

    return parser


class Formatter(argparse.HelpFormatter):
    def _format_action(self, action):
        if isinstance(action, argparse._SubParsersAction):
            parts = []
            for i in action._get_subactions():
                parts.append("%*s%-21s %s" % (self._current_indent, "", i.metavar, i.help))
            return "\n".join(parts)
        return super(Formatter, self)._format_action(action)



def main():
    if not is_virt_enabled():
        print("Virtualization not enabled")
        exit(1)
    parser = get_parser()
    if USE_ARGCOMPLETE:
        argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if not args.command:
        parser.print_help()
        parser.error("Please specify a command")

    tb = Thinbox()
    if args.command == "pull":
        tb.pull(tag=args.tag, url=args.url)
    elif args.command == "image":
        tb.image()
    elif args.command == "create":
        if args.image:
            tb.create_from_image(args.image, args.name)
    elif args.command == "copy":
        tb.copy(args.file, args.name, args.dir, args.pre, args.comm)
    elif args.command == "enter":
        tb.enter(args.name)
    elif args.command == "remove":
        tb.remove(args.name)
    elif args.command == "start":
        tb.start(args.name)
    elif args.command == "stop":
        if args.force:
            tb.stop(args.name, "--mode=acpi")
        tb.stop(args.name)
    elif args.command == "list" or args.command == "ls":
        if args.all:
            tb.list()
        elif args.other:
            tb.list(fil="other")
        elif args.paused:
            tb.list(fil="paused")
        elif args.running:
            tb.list(fil="running")
        elif args.stopped:
            tb.list(fil="stopped")
        else:
            tb.list()
    elif args.command == "remove" or args.command == "rm":
        if args.all:
            tb.remove_all()
        else:
            tb.remove(args.name)
    elif args.command == "vm":
        if args.vm_parser == "list" or args.vm_parser == "ls":
            if args.all:
                tb.list()
            elif args.other:
                tb.list(fil="other")
            elif args.paused:
                tb.list(fil="paused")
            elif args.running:
                tb.list(fil="running")
            elif args.stopped:
                tb.list(fil="stopped")
            else:
                tb.list()
        elif args.vm_parser == "remove" or args.vm_parser == "rm":
            if args.all:
                tb.remove_all()
            else:
                tb.remove(args.name)
        else:
            tb.list()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as ex:
        print("Error:", ex, file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
