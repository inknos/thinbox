import libvirt


class Domain(object):
    """Class made to represent a libvirt domain

    :param name: Domain's name
    :type name: str

    :param id: Domain's IP
    :type id: int

    :param active: Domain's active state
    :type active: int

    :param uuid: Domain's UUID
    :type uuid: str

    :param ip: Domain's IP
    :type ip: str

    :param mac: Domain's MAC
    :type mac: str

    :param state: Domain's State
    :type state: str

    :param reason: Domain's state reason
    :type reason: str

    """

    def __init__(self, domain):
        """Constructor, takes a libvirt.domain as parameter
        """
        super().__init__()
        self._dom = domain
        self._name = domain.name()
        self._id = domain.ID()
        self._active = domain.isActive()
        self._uuid = domain.UUIDString()

        # need to be updated more than once
        self._state = ""
        self._reason = ""
        self._addr = {}
        self._ip = ""
        self._mac = ""

    @property
    def name(self):
        """Return domain's name

        :rtype: str
        """
        return self._name

    @property
    def id(self):
        """Return domain's ID

        :rtype: int
        """
        return self._id

    @property
    def active(self):
        """Return if domain is active

        :return: `1` if active, `0` otherwise
        :rtype: int
        """
        self._active = self._dom.isActive()
        return self._active

    @property
    def uuid(self):
        """Return domain's UUID

        :rtype: str
        """
        return self._uuid

    @property
    def ip(self):
        """Return domain's IP

        :return: Empty string if IP not found
        :rtype: str
        """
        if self._ip == "":
            self._set_ip_from_addr()
        return self._ip

    @property
    def mac(self):
        """Return domain's MAC

        :return: Empty string if MAC not found
        :rtype: str
        """
        if self._mac == "":
            self._set_mac_from_addr()
        return self._mac

    @property
    def state(self):
        """Return domain's state

        :rtype: str
        """
        self._set_state_reason()
        return self._state

    @property
    def reason(self):
        """Return domain's reason

        :rtype: str
        """
        self._set_state_reason()
        return self._reason

    def shutdown(self):
        """Shutdown domain

        Call libvirt.virDomain.shutdown()

        :rtype: int
        """
        return self._dom.shutdown()

    def start(self):
        """Start domain

        Call libvirt.virDomain.create()

        :rtype: int
        """
        return self._dom.create()

    def destroy(self):
        """Destroy domain

        Call libvirt.virDomain.destroy()

        :rtype: int
        """
        return self._dom.destroy()

    def undefine(self):
        """Undefine domain

        Call libvirt.virDomain.undefine()

        :rtype: int
        """
        return self._dom.undefine()

    def _set_state_reason(self):
        """Return domain's state and reason

        Call libvirt.virDomain.state()

        :returns: State and reason
        :rtype: tuple
        """
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
        try:
            self._addr = self._dom.interfaceAddresses(
                libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_ARP
            )
        except libvirt.libvirtError as e:
            logging.debug("libvirt: {}".format(e))

    def _set_ip_from_addr(self):
        """Sets new IP if empty str
        """
        self._set_addr()
        if self._addr == {}:
            return
        tapx = list((self._addr))[0]
        self._ip = self._addr[tapx]['addrs'][0]['addr']

    def _set_mac_from_addr(self):
        """Sets new MAC if empty str
        """
        self._set_addr()
        if self._addr == {}:
            self._mac = ""
            return
        tapx = list((self._addr))[0]
        self._mac = self._addr[tapx]['hwaddr']


class LibVirtConnection(object):
    """Represent libvirt.virConnection object

    :param conn: Connection to libvirt
    :type conn: libvirt.virConnectiion

    :param doms: Domains
    :type doms: list
    """
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
        """Open a libvirt connection and return it

        :param readonly: Open readonly connection
        :type readonly: bool

        :return: Libvirt connection
        :rtype: libvirt.virConnection
        """
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
        """Get domain by name

        :param name: Name of domain to get
        :type name: str

        :return: Domain by name
        :rtype: libvirt.virDomain
        """
        try:
            dom = self.conn.lookupByName(name)
        except libvirt.libvirtError as e:
            logging.error("libvirt: {}").format(e)
            sys.exit(1)
        return dom

    def _get_all_domains(self):
        """Get all domains

        :return: All Domains
        :rtype: list
        """
        return [Domain(d) for d in self.conn.listAllDomains()]
