import re
import socket
import requests
import os
import subprocess
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
    env = os.environ.copy()
    env["LC_LANG"] = "C"
    out = subprocess.run(["lscpu"], env=env, stdout=subprocess.PIPE)
    return "VT-x" in str(out.stdout)


def create_ssh_connection(hostname, username="root", port=22):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
    client.connect(hostname=hostname, username=username, port=port)
    return client


def run_ssh_command(session, cmd):
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

    Parameters
    ----------
    name : str
        Machine name
    """
    logging.debug("options: {}".format(THINBOX_SSH_OPTIONS))
    os.system("ssh {} root@{}".format(THINBOX_SSH_OPTIONS, dom.ip))


def download_file(url, filepath):
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
                sys.stdout.write('\r[{}{}]'.format(
                    '█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')
    return True
