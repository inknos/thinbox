import libvirt

class Domain(object):
    """
    Class made to represent a libvirt domain

    Parameters
    ----------

    name : str
    id : int
    active : int
    uuid : str
    ip : str
    mac : str
    state : str
    reason : str

    Methods
    -------

    shutdown
    start
    """
    def __init__(self, domain):
        super().__init__()
        self._dom    = domain
        self._name   = domain.name()
        self._id     = domain.ID()
        self._active = domain.isActive()
        self._uuid   = domain.UUIDString()

        # need to be updated more than once
        self._state = ""
        self._reason= ""
        self._addr   = {}
        self._ip = ""
        self._mac = ""

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def active(self):
        return self._active

    @property
    def uuid(self):
        return self._uuid

    @property
    def ip(self):
        if self._ip == "":
            self._set_ip_from_addr()
        return self._ip

    @property
    def mac(self):
        if self._mac == "":
            self._set_mac_from_addr()
        return self._mac

    @property
    def state(self):
        self._set_state_reason()
        return self._state

    @property
    def reason(self):
        self._set_state_reason()
        return self._reason

    def shutdown(self):
        self._dom.shutdown()

    def start(self):
        self._dom.create()

    def _set_state_reason(self):
        state, reason = self._dom.state()

        if state == libvirt.VIR_DOMAIN_NOSTATE:
            self._state == "nostate"
        elif state == libvirt.VIR_DOMAIN_RUNNING:
            self._state = "running"
        elif state == libvirt.VIR_DOMAIN_BLOCKED:
            self._state = "blocked"
        elif state == libvirt.VIR_DOMAIN_PAUSED:
            self._state = "paused"
        elif state == libvirt.VIR_DOMAIN_SHUTDOWN:
            self._state = "shutdown"
        elif state == libvirt.VIR_DOMAIN_SHUTOFF:
            self._state = "shutoff"
        elif state == libvirt.VIR_DOMAIN_CRASHED:
            self._state = "crashed"
        elif state == libvirt.VIR_DOMAIN_PMSUSPENDED:
            self._state = "pmsuspended"
        else:
            self._state = "unknown"
        self._reason = str(reason)

    def _set_addr(self):
        """Sets new addr if empty
        """
        if self.active == 0:
            return
        if self._addr == {}:
            try:
                self._addr = self._dom.interfaceAddresses(
                    libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_ARP
                )
            except libvirt.libvirtError as e:
                logging.debug("libvirt: {}".format(e))

    def _set_ip_from_addr(self):
        self._set_addr()
        if self._addr == {}:
            self._ip = ""
            return
        tapx = list((self._addr))[0]
        self._ip = self._addr[tapx]['addrs'][0]['addr']

    def _set_mac_from_addr(self):
        self._set_addr()
        if self._addr == {}:
            self._mac = ""
            return
        tapx = list((self._addr))[0]
        self._mac = self._addr[tapx]['hwaddr']


class LibVirtConnection(object):
    def __init__(self, readonly=True):
        super().__init__()
        self._conn = self._get_connection(readonly)
        self._doms = self._get_all_domains()

    @property
    def conn(self):
        return self._conn

    @property
    def doms(self):
        return self._doms

    def _get_connection(self, readonly):
        try:
            if readonly:
                conn = libvirt.openReadOnly(None)
            else:
                conn = libvirt.open()
        except libvirt.libvirtError as e:
            logging.error("libvirt: {}".format(e))
            sys.exit(1)
        return conn

    def _get_domain(self, name):
        try:
            dom = self.conn.lookupByName(name)
        except libvirt.libvirtError as e:
            logging.error("libvirt: {}").format(e)
            sys.exit(1)
        return dom

    def _get_all_domains(self):
        return [ Domain(d) for d in self.conn.listAllDomains() ]

