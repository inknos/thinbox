import re
import socket
import requests
import os
import subprocess
import sys
import logging
import paramiko

from bs4 import BeautifulSoup
from scp import SCPClient
from urllib.parse import urlparse
from time import sleep

from thinbox.config import THINBOX_SSH_OPTIONS


def _url_is_valid(url):
    """Validate a url format based on Django validator

    The validation is done through regex and it was taken from:
    https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
    https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45

    :parameter url: The url to validate
    :type url: str

    :return: True if the url is valid
    :rtype: bool
    """

    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def _ping_server(server: str, port=443, timeout=3):
    """ping server"""
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server, port))
    except OSError as error:
        return False
    else:
        s.close()
        return True


def is_virt_enabled():
    """Detect if virtualization is enabled

    :return: True if enabled
    :rtype: bool
    """
    env = os.environ.copy()
    env["LC_LANG"] = "C"
    out = subprocess.run(["lscpu"], env=env, stdout=subprocess.PIPE)
    return "VT-x" in str(out.stdout)


def create_ssh_connection(hostname, username="root", port=22):
    """Create and return ssh connection

    :param hostname: Hostname to ssh in
    :type hostname: str

    :parmam username: Username for ssh connection, defaults to "root"
    :type username: str

    :param port: Port to connect, defaults to 22
    :type port: int

    :return: Ssh connection
    :rtype: paramiko.SSHClient
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
    client.connect(hostname=hostname, username=username, port=port)
    return client


def run_ssh_command(session, cmd):
    """Run command in ssh session

    :param session: SSH session
    :type session: paramiko.SSHClient

    :param cmd: Command to run
    :type cmd: str
    """
    logging.debug("Command", cmd)

    ssh_stdin, ssh_stdout, ssh_stderr = session.exec_command(cmd)
    exit_code = ssh_stdout.channel.recv_exit_status()  # handles async exit error

    for line in ssh_stdout:
        print(line.strip())

    if exit_code != 0:
        logging.warning("paramiko error: {}".format(exit_code))
        for line in ssh_stderr:
            logging.warning("paramiko stderr: {}".format(line.strip()))


def _image_name_wrong(name):
    """Checks base image name

    :param name: Name of image to check
    :type name: str

    :returns: True if valid
    :rtype: bool
    """
    return name.endswith(".qcow2")


def logging_subprocess(process, output):
    for so in process.stdout.read().decode('utf8').split('\n'):
        if so == '':
            continue
        logging.debug(output.format(so))
    for se in process.stderr.read().decode('utf8').split('\n'):
        if se == '':
            continue
        logging.error(output.format(se))


def ssh_connect(dom):
    """Connect and open interactive ssh shell

    :parameter name: Machine name
    :type name: str
    """
    logging.debug("options: {}".format(THINBOX_SSH_OPTIONS))
    os.system("ssh {} root@{}".format(THINBOX_SSH_OPTIONS, dom.ip))


def download_file(url, filepath):
    """Download file from url to specific path

    Prints nice status bar

    :parameter url: Location of file to be downloaded
    :type url: str

    :parameter path: Path where the file will be saved
    :type path: str

    :return: True if file is successfully downloaded
    :rtype: bool
    """
    if not _url_is_valid(url):
        logger.warning("URL may be in not valid format.")

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
                sys.stdout.write('\r{}:\t[{}{}]'.format(
                    os.path.basename(filepath),
                    '█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')
    return True

def printd(text, delay=.5):
    """Prints string with ending dots

    :param text: String to print
    :type text: str

    :param delay: Delay in seconds, defaults to .5
    :type delay: float, optional
    """
    print(end=text)
    n_dots = 0

    while True:
        if n_dots == 3:
            print(end='\b\b\b', flush=True)
            print(end='   ',    flush=True)
            print(end='\b\b\b', flush=True)
            n_dots = 0
        else:
            print(end='.', flush=True)
            n_dots += 1
        sleep(delay)

def os_variant(image):
    """Guess OS-Variant to init virtual machine

    :param image: Name of image to guess
    :type name: str

    :return: valid os_variant
    :rtype: str
    """
    if "rhel" in image:
        if "8.6" in image:
            return "none"
        elif "8.5" in image:
            return "rhel8.5"
    elif "fedora" in image or "Fedora" in image:
        if "34" in image:
            return "fedora34"
        elif "35" in image:
            return "feora35"
    else:
        return "none"

