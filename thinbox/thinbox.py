from thinbox import domain
from thinbox.utils import *
from thinbox.config import *

class Thinbox(object):
    """
    A class made to represent a Thinbox run

    Attributes
    ----------
    all_domains : list
        list of names of all domains

    all_running_domains : list
        list of names of all running domains

    all_stopped_domains : list
        list of names of all stopped domains

    all_paused_domains : list
        list of names of all paused domains

    all_other_domains : list
        list of names of all other domains

    base_images : list
        list of all base images available

    base_dir : str
        Directory where base images are stored

    image_dir : str
        Directory where vm images are stored

    hash_dir : str
        Directory where hashes are stored


    Methods
    -------
    pull(tag=None, url=None)
        Pulls a base image from a url or from a tag

    enter(name)
        Enter domain
    """

    def __init__(self, readonly=True):
        super().__init__()
        self._readonly = readonly
        self._doms = self._get_all_domains(readonly)
        self._base_dir = THINBOX_BASE_DIR
        self._image_dir = THINBOX_IMAGE_DIR
        self._hash_dir = THINBOX_HASH_DIR
        self._create_cache_dirs()
        self._base_images = self._get_base_images()

    def _create_cache_dirs(self):
        self._create_dir("Base cache", self.base_dir)
        self._create_dir("Image cache", self.image_dir)
        self._create_dir("Hash cache", self.hash_dir)

    def _create_dir(self, dirname, dirpath):
        if os.path.exists(dirpath) and not os.path.isdir(dirpath):
            logging.error("{} dir {} exists and it's not a directory.".format(dirname, dirpath))
            sys.exit(1)
        elif not os.path.exists(dirpath):
            os.mkdir(dirpath)
            logging.debug("{} dir not existing. Created on {}.".format(dirname, dirpath))

    @property
    def doms(self):
        self._get_all_domains(self._readonly)
        return self._doms

    @property
    def base_images(self):
        return self._base_images

    @property
    def base_dir(self):
        """Directory where base images are stored

        Defaults to $XDG_CACHE_HOME/thinbox/base

        Imported from env var THINBOX_BASE_DIR

        Returns
        -------
        Path of base images
        """
        return self._base_dir

    @property
    def image_dir(self):
        """Directory where vm images are stored

        Defaults to $XDG_CACHE_HOME/thinbox/images

        Imported from env var THINBOX_IMAGE_DIR

        Returns
        -------
        Path of vm images
        """
        return self._image_dir

    @property
    def hash_dir(self):
        """Directory where hashes are stored

        Defaults to $XDG_CACHE_HOME/thinbox/hash

        Imported from env var THINBOX_HASH_DIR

        Returns
        -------
        Path of hashes
        """
        return self._hash_dir


    def stop(self, name, opt=None):
        """Stop running domain

        Parameters
        ----------
        name : str
            Name of domain to stop

        opt : str, optional
            Options to pass to virsh command
            Options are None, "--mode=acpi"
        """
        dom = self._get_dom_from_name(name)
        if dom.active == 0:
            print("Domain '{}' already stopped.".format(dom.name))
            return
        # TODO mode acpi
        #if opt == "--mode=acpi":
        #    dom.shutdown()
        dom.shutdown()
        print("Domain '{}' is being shutdown.".format(dom.name))

    def start(self, name):
        """Start a domain

        Parameters
        ----------

        name : str
            Name of domain to start
        """
        dom = self._get_dom_from_name(name)

        if dom.active == 1:
            print("Domain '{}' is already running.".format(dom.name))
            print("To SSH in it run: thinbox enter {}".format(dom.name))
            return
        dom.start()
        print("Domain '{}' started.".format(dom.name))
        print("To SSH into it run: thinbox enter {}".format(dom.name))

    def remove(self, name):
        """Remove a domain of given name

        Parameters
        ---------
        name : str
            Name of domain to remove
        """
        dom = self._get_dom_from_name(name)

        # stop the domain
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
        filepath = os.path.join(self.image_dir, name + ".qcow2")
        if os.path.exists(filepath):
            os.remove(filepath)
        else:
            logging.warning("File does not exist: {}".format(filepath))

    def remove_all(self):
        """Remove all domains
        """
        domains = self.doms
        for d in domains:
            self.remove(d.name)

    def pull_url(self, url, skip=True):
        """Download a qcow2 image file from url

        Parameters
        ----------
        url : str
            Url of image to download
        """
        print("Pulling {}".format(url))
        self._download_image(url)

    def pull_tag(self, tag, skip=True):
        """Download a qcow2 image file from tag

        Parameters
        ----------
        tag : str
            Tag of image to download (RHEL only)
        """
        if tag not in RHEL_TAGS:
            print("Tag '{}' is not a known tag")
            sys.exit(1)

        if not RHEL_IMAGE_URL:
            logging.warning(
                "Variable RHEL_IMAGE_URL. If you know where to pull images please export this variable locally.")
            sys.exit(1)
        url = self._generate_url_from_tag(tag)
        self.pull_url(url)

    def image_list(self):
        """Print a list of base images on the system
        """
        print(self.base_dir)
        print()
        print("{:<50} {:<20}".format("IMAGE", "HASH"))
        for name in self.base_images:
            print("{:<50} ".format(name), end="")
            none = True
            hashes = []
            for hashfunc in sorted(RHEL_IMAGE_HASH):
                if os.path.exists(os.path.join(self.hash_dir, name + "." + hashfunc + ".OK")):
                    hashes.append(hashfunc)
                    none = False
            if none:
                print("NONE", end="")
            else:
                print(",".join(hashes), end="")

            print()

    def image_remove(self, name):
        # check if image exist
        if name not in self.base_images:
            logging.warning("Image '{}' not found".format(name))
            return

        filepath = os.path.join(self.base_dir, name)
        os.remove(filepath)
        print("Image '{}' removed.".format(name))

    def image_remove_all(self):
        for name in self.base_images:
            self.image_remove(name)

    def copy(self, files, name, directory="/root", pre="", command=""):
        """Copy file or files into a running domain

        Parameters
        ----------
        files : list
            List of files to copy in the domain

        name : str
            Name of domain to copy file/files in

        command :  str, optional
            Command to run inside the domain after files are copied

        directory : str, optional
            Destination directory for files to be copied in. (default is "/root")

        pre : str, optional
            Command to run inside the domain before the files are copied
        """
        # domain exist?
        # TODO domain exist
        #if not _domain_exists(name):
        #    logging.error(
        #        "Domain with name '{}' does not exist.".format(name))
        #    sys.exit(1)
        # TODO
        # is domain running?
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
        """List domains

        Parameters
        ----------
        fil : str, optional
            Filter domains by state
            Options are "", "running", "stopped", "paused", "other"
        """
        def state_filter(d):
            if d.state == fil:
                return True
            return False

        if fil == "":
            domains = self.doms
        else:
            domains = [ d for d in filter(state_filter, self.doms) ]

        if len(domains) == 0:
            print("To create a domain run: thinbox create -i <image> <name>")
            return
        print_format = "{:<20} {:<8} {:<16} {:<10}"
        print(print_format.format("DOMAIN", "STATE", "IP", "MAC"))
        for d in domains:
            print(print_format.format(d.name, d.state, d.ip, d.mac))

    def image_rm(self):
        pass

    def enter(self, name):
        """Enter domain via ssh

        If domain is stopped, start it

        Parameters
        ----------
        dom : str
            Domain to ssh into
        """
        dom = self._get_dom_from_name(name)
        # if domain is not up, start it
        if dom.active == 0:
            dom.start()

        self._wait_for_boot(dom)
        print("Connecting to domain '{}' as root@{}".format(dom.name, dom.ip))
        ssh_connect(dom)

    def create(self):
        print("create")

    def create_from_image(self, base_name, name):

        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        image = os.path.join(self.image_dir, name + ".qcow2")
        base = os.path.join(self.base_dir, base_name)
        if not os.path.exists(base):
            logging.error("Image {} not found in {}.".format(
                base, self.base_dir))
            if not _image_name_wrong(base):
                print("Maybe the filename is incorrect?")
            print("To list the available images run: thinbox image")
            sys.exit(1)

        # ensure_domain_undefined $name

        # if _domain_exists(name):
        #    logging.error("Domain with name '{}' exists.".format(name))
        #    sys.exit(1)

        p_qemu = subprocess.Popen([
            'qemu-img', 'create',
            '-f', 'qcow2', '-o',
            'backing_file=' + base + ',backing_fmt=qcow2', image],
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

    def _get_dom_from_name(self, name):
        domains = [ d for d in self.doms if d.name == name ]
        if domains == []:
            print("Domain '{}' does not exist".format(name))
            sys.exit(1)
        elif len(domains) > 1:
            logging.error("Found more than one domain with name '{}'".format(name))
        return domains[0]

    def _wait_for_boot(self, dom):
        def printd(text, delay=.5):
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

        while dom.ip == "":
            printd("Domain '{}' is starting".format(dom.name))
            sleep(1)
            dom.ip

    def _get_all_domains(self, readonly):
        conn = domain.LibVirtConnection(readonly)
        return conn.doms

    def _get_base_images(self):
        image_list = []
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                image_list.append(file)
        return image_list

    def _generate_url_from_tag(self, tag):
        url = RHEL_IMAGE_URL
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        links = soup.select("a")
        return os.path.join(url, links[12].text)

    def _download_image(self, url):
        filename = os.path.split(url)[-1]
        filepath = os.path.join(self.base_dir, filename)
        # check dir exist
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        _download_file(url, filepath)
        # TODO download hash
        # this works for rhel
        if urlparse(url).netloc in RHEL_IMAGE_DOMAIN:
            hashpath = os.path.join(self.hash_dir, filename)
            for ext in RHEL_IMAGE_HASH:
                _download_file(url + "." + ext, hashpath + "." + ext)
        if self.check_hash(filename, "sha256"):
            print("Image downloaded, verified, and ready to use")
        else:
            print("Image downloaded and ready to use but not verified.")

    def _check_hash(self, filename, ext, hashfunc):
        """"This function returns the SHA-1 hash
        of the file passed into it"""
        h = hashfunc
        filepath = os.path.join(self.base_dir, filename)
        hashpath = os.path.join(self.hash_dir, filename + "." + ext)
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
        with open(filepath, 'rb') as file:
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

    def check_hash(self, filename, hashname="md5"):
        """Check hash of file

        Parameters
        ----------
        filename : str
            Name of the file to check

        hashname : str, optional
            Type of hash

        Returns
        -------
        result : bool
            True if hashes match
        """
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
            logging.error("Not a valid hash function: {}".format(hashname))
        result, hh, hf = self._check_hash(filename, ext, hashfunc)

        logging.debug("File hash is {}.".format(hf))
        logging.debug("Expected {} is {}.".format(hashname, hh))
        if not result:
            logging.info("Continue withouth hash verification")
            return result
        if not hh == hf:
            logging.error("Hashes do not match")
            sys.exit(1)

        return result


