# -*- coding: iso-8859-1 -*-
# Copyright (C) 2003, 2004 Nominum, Inc.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose with or without fee is hereby granted,
# provided that the above copyright notice and this permission notice
# appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NOMINUM DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NOMINUM BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""DNS stub resolver.

@var default_resolver: The default resolver object
@type default_resolver: linkcheck.dns.resolver.Resolver object"""

import socket
import sets
import sys
import os
import time

import linkcheck.dns.exception
import linkcheck.dns.message
import linkcheck.dns.name
import linkcheck.dns.query
import linkcheck.dns.rcode
import linkcheck.dns.rdataclass
import linkcheck.dns.rdatatype

if sys.platform == 'win32':
    import _winreg

class NXDOMAIN(linkcheck.dns.exception.DNSException):
    """The query name does not exist."""
    pass

# The definition of the Timeout exception has moved from here to the
# linkcheck.dns.exception module.  We keep linkcheck.dns.resolver.Timeout defined for
# backwards compatibility.

Timeout = linkcheck.dns.exception.Timeout

class NoAnswer(linkcheck.dns.exception.DNSException):
    """The response did not contain an answer to the question."""
    pass

class NoNameservers(linkcheck.dns.exception.DNSException):
    """No non-broken nameservers are available to answer the query."""
    pass

class Answer(object):
    """DNS stub resolver answer

    Instances of this class bundle up the result of a successful DNS
    resolution.

    For convenience, the answer is iterable.  "for a in answer" is
    equivalent to "for a in answer.rrset".

    Note that CNAMEs or DNAMEs in the response may mean that answer
    node's name might not be the query name.

    @ivar qname: The query name
    @type qname: linkcheck.dns.name.Name object
    @ivar rdtype: The query type
    @type rdtype: int
    @ivar rdclass: The query class
    @type rdclass: int
    @ivar response: The response message
    @type response: linkcheck.dns.message.Message object
    @ivar rrset: The answer
    @type rrset: linkcheck.dns.rrset.RRset object
    @ivar expiration: The time when the answer expires
    @type expiration: float (seconds since the epoch)
    """
    def __init__(self, qname, rdtype, rdclass, response):
        self.qname = qname
        self.rdtype = rdtype
        self.rdclass = rdclass
        self.response = response
        min_ttl = -1
        rrset = None
        for count in xrange(0, 15):
            try:
                rrset = response.find_rrset(response.answer, qname,
                                            rdclass, rdtype)
                if min_ttl == -1 or rrset.ttl < min_ttl:
                    min_ttl = rrset.ttl
                break
            except KeyError:
                if rdtype != linkcheck.dns.rdatatype.CNAME:
                    try:
                        crrset = response.find_rrset(response.answer,
                                                     qname,
                                                     rdclass,
                                                     linkcheck.dns.rdatatype.CNAME)
                        if min_ttl == -1 or crrset.ttl < min_ttl:
                            min_ttl = crrset.ttl
                        for rd in crrset:
                            qname = rd.target
                            break
                        continue
                    except KeyError:
                        raise NoAnswer("DNS response had no answer")
                raise NoAnswer("DNS response had no answer")
        if rrset is None:
            raise NoAnswer("DNS response had no answer")
        self.rrset = rrset
        self.expiration = time.time() + min_ttl

    def __getattr__(self, attr):
        if attr == 'name':
            return self.rrset.name
        elif attr == 'ttl':
            return self.rrset.ttl
        elif attr == 'covers':
            return self.rrset.covers
        elif attr == 'rdclass':
            return self.rrset.rdclass
        elif attr == 'rdtype':
            return self.rrset.rdtype
        else:
            raise AttributeError, attr

    def __len__(self):
        return len(self.rrset)

    def __iter__(self):
        return iter(self.rrset)

class Cache(object):
    """Simple DNS answer cache.

    @ivar data: A dictionary of cached data
    @type data: dict
    @ivar cleaning_interval: The number of seconds between cleanings.  The
    default is 300 (5 minutes).
    @type cleaning_interval: float
    @ivar next_cleaning: The time the cache should next be cleaned (in seconds
    since the epoch.)
    @type next_cleaning: float
    """

    def __init__(self, cleaning_interval=300.0):
        """Initialize a DNS cache.

        @param cleaning_interval: the number of seconds between periodic
        cleanings.  The default is 300.0
        @type cleaning_interval: float.
        """

        self.data = {}
        self.cleaning_interval = cleaning_interval
        self.next_cleaning = time.time() + self.cleaning_interval

    def maybe_clean(self):
        """Clean the cache if it's time to do so."""

        now = time.time()
        if self.next_cleaning <= now:
            keys_to_delete = []
            for (k, v) in self.data.iteritems():
                if v.expiration <= now:
                    keys_to_delete.append(k)
            for k in keys_to_delete:
                del self.data[k]
            now = time.time()
            self.next_cleaning = now + self.cleaning_interval

    def get(self, key):
        """Get the answer associated with I{key}.  Returns None if
        no answer is cached for the key.
        @param key: the key
        @type key: (linkcheck.dns.name.Name, int, int) tuple whose values are the
        query name, rdtype, and rdclass.
        @rtype: linkcheck.dns.resolver.Answer object or None
        """

        self.maybe_clean()
        v = self.data.get(key)
        if v is None or v.expiration <= time.time():
            return None
        return v

    def put(self, key, value):
        """Associate key and value in the cache.
        @param key: the key
        @type key: (linkcheck.dns.name.Name, int, int) tuple whose values are the
        query name, rdtype, and rdclass.
        @param value: The answer being cached
        @type value: linkcheck.dns.resolver.Answer object
        """
        self.maybe_clean()
        self.data[key] = value

    def flush(self, key=None):
        """Flush the cache.

        If I{key} is specified, only that item is flushed.  Otherwise
        the entire cache is flushed.

        @param key: the key to flush
        @type key: (linkcheck.dns.name.Name, int, int) tuple or None
        """
        if not key is None:
            if self.data.has_key(key):
                del self.data[key]
        else:
            self.data = {}
            self.next_cleaning = time.time() + self.cleaning_interval


class Resolver(object):
    """DNS stub resolver

    @ivar domain: The domain of this host
    @type domain: linkcheck.dns.name.Name object
    @ivar nameservers: A list of nameservers to query.  Each nameserver is
    a string which contains the IP address of a nameserver.
    @type nameservers: list of strings
    @ivar search: The search list.  If the query name is a relative name,
    the resolver will construct an absolute query name by appending the search
    names one by one to the query name.
    @type search: list of linkcheck.dns.name.Name objects
    @ivar port: The port to which to send queries.  The default is 53.
    @type port: int
    @ivar timeout: The number of seconds to wait for a response from a
    server, before timing out.
    @type timeout: float
    @ivar lifetime: The total number of seconds to spend trying to get an
    answer to the question.  If the lifetime expires, a Timeout exception
    will occur.
    @type lifetime: float
    @ivar keyring: The TSIG keyring to use.  The default is None.
    @type keyring: dict
    @ivar keyname: The TSIG keyname to use.  The default is None.
    @type keyname: linkcheck.dns.name.Name object
    @ivar edns: The EDNS level to use.  The default is -1, no Elinkcheck.dns.
    @type edns: int
    @ivar ednsflags: The EDNS flags
    @type ednsflags: int
    @ivar payload: The EDNS payload size.  The default is 0.
    @type payload: int
    @ivar cache: The cache to use.  The default is None.
    @type cache: linkcheck.dns.resolver.Cache object
    """
    def __init__(self, filename='/etc/resolv.conf', configure=True):
        """Initialize a resolver instance.

        @param filename: The filename of a configuration file in
        standard /etc/resolv.conf format.  This parameter is meaningful
        only when I{configure} is true and the platform is POSIX.
        @type filename: string or file object
        @param configure: If True (the default), the resolver instance
        is configured in the normal fashion for the operating system
        the resolver is running on.  (I.e. a /etc/resolv.conf file on
        POSIX systems and from the registry on Windows systems.)
        @type configure: bool"""

        self.reset()
        if configure:
            if sys.platform == 'win32':
                self.read_registry()
            elif filename:
                self.read_resolv_conf(filename)
                self.read_local_hosts()

    def reset(self):
        """Reset all resolver configuration to the defaults."""
        self.domain = \
            linkcheck.dns.name.Name(linkcheck.dns.name.from_text(socket.gethostname())[1:])
        if len(self.domain) == 0:
            self.domain = linkcheck.dns.name.root
        self.nameservers = []
        self.localhosts = sets.Set([
          'localhost',
          'loopback',
          '127.0.0.1',
          '::1',
          'ip6-localhost',
          'ip6-loopback',
        ])
        self.search = []
        self.search_patters = ['www.%s.com', 'www.%s.org', 'www.%s.net', ]
        self.port = 53
        self.timeout = 2.0
        self.lifetime = 30.0
        self.keyring = None
        self.keyname = None
        self.edns = -1
        self.ednsflags = 0
        self.payload = 0
        self.cache = None

    def read_resolv_conf(self, f):
        """Process f as a file in the /etc/resolv.conf format.  If f is
        a string, it is used as the name of the file to open; otherwise it
        is treated as the file itself."""
        if isinstance(f, str) or isinstance(f, unicode):
            f = open(f, 'r')
            want_close = True
        else:
            want_close = False
        try:
            for l in f:
                l = l.strip()
                if len(l) == 0 or l[0] == '#' or l[0] == ';':
                    continue
                tokens = l.split()
                if len(tokens) < 2:
                    continue
                if tokens[0] == 'nameserver':
                    self.nameservers.append(tokens[1])
                elif tokens[0] == 'domain':
                    self.domain = linkcheck.dns.name.from_text(tokens[1])
                elif tokens[0] == 'search':
                    for suffix in tokens[1:]:
                        self.search.append(linkcheck.dns.name.from_text(suffix))
        finally:
            if want_close:
                f.close()
        if len(self.nameservers) == 0:
            self.nameservers.append('127.0.0.1')

    def read_local_hosts (self):
        # XXX is this default list of localhost stuff complete?
        self.add_addrinfo(socket.gethostname())
        # add system specific hosts for all enabled interfaces
        for addr in self.read_local_ifaddrs():
            self.add_addrinfo(addr)

    def read_local_ifaddrs (self):
        """all active interfaces' ip addresses"""
        if os.name!='posix':
            # only posix is supported
            return []
        import linkcheck.dns.ifconfig
        ifc = linkcheck.dns.ifconfig.IfConfig()
        return [ ifc.getAddr(iface) for iface in ifc.getInterfaceList()
                 if ifc.isUp(iface) ]

    def add_addrinfo (self, host):
        try:
            addrinfo = socket.gethostbyaddr(host)
        except socket.error:
            self.localhosts.add(host.lower())
            return
        self.localhosts.add(addrinfo[0].lower())
        for h in addrinfo[1]:
            self.localhosts.add(h.lower())
        for h in addrinfo[2]:
            self.localhosts.add(h.lower())

    def _config_win32_nameservers(self, nameservers, split_char=','):
        """Configure a NameServer registry entry."""
        # we call str() on nameservers to convert it from unicode to ascii
        ns_list = str(nameservers).split(split_char)
        for ns in ns_list:
            if not ns in self.nameservers:
                self.nameservers.append(ns)

    def _config_win32_domain(self, domain):
        """Configure a Domain registry entry."""
        # we call str() on domain to convert it from unicode to ascii
        self.domain = linkcheck.dns.name.from_text(str(domain))

    def _config_win32_search(self, search):
        """Configure a Search registry entry."""
        # we call str() on search to convert it from unicode to ascii
        search_list = str(search).split(',')
        for s in search_list:
            if not s in self.search:
                self.search.append(linkcheck.dns.name.from_text(s))

    def _config_win32_add_ifaddr (self, key, name):
        """Add interface ip address to self.localhosts."""
        try:
            ip, rtype = _winreg.QueryValueEx(key, name)
            if isinstance(ip, basestring) and ip:
                self.localhosts.add(str(ip).lower())
        except WindowsError:
            pass

    def _config_win32_fromkey(self, key):
        """Extract DNS info from a registry key."""
        try:
            enable_dhcp, rtype = _winreg.QueryValueEx(key, 'EnableDHCP')
        except WindowsError:
            enable_dhcp = False
        if enable_dhcp:
            try:
                servers, rtype = _winreg.QueryValueEx(key, 'DhcpNameServer')
            except WindowsError:
                servers = None
            if servers:
                # Annoyingly, the DhcpNameServer list is apparently space
                # separated instead of comma separated like NameServer.
                self._config_win32_nameservers(servers, ' ')
                try:
                    dom, rtype = _winreg.QueryValueEx(key, 'DhcpDomain')
                    if dom:
                        self._config_win32_domain(servers)
                except WindowsError:
                    pass
            self._config_win32_add_ifaddr(key, 'DhcpIPAddress')
        else:
            try:
                servers, rtype = _winreg.QueryValueEx(key, 'NameServer')
            except WindowsError:
                servers = None
            if servers:
                self._config_win32_nameservers(servers)
                try:
                    dom, rtype = _winreg.QueryValueEx(key, 'Domain')
                    if dom:
                        self._config_win32_domain(servers)
                except WindowsError:
                    pass
            self._config_win32_add_ifaddr(key, 'IPAddress')
        try:
            search, rtype = _winreg.QueryValueEx(key, 'SearchList')
        except WindowsError:
            search = None
        if search:
            self._config_win32_search(servers)

    def read_registry(self):
        """Extract resolver configuration from the Windows registry."""
        lm = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
        want_scan = False
        try:
            try:
                # XP, 2000
                tcp_params = _winreg.OpenKey(lm,
                                             r'SYSTEM\CurrentControlSet'
                                             r'\Services\Tcpip\Parameters')
                want_scan = True
            except EnvironmentError:
                # ME
                tcp_params = _winreg.OpenKey(lm,
                                             r'SYSTEM\CurrentControlSet'
                                             r'\Services\VxD\MSTCP')
            try:
                self._config_win32_fromkey(tcp_params)
            finally:
                tcp_params.Close()
            if want_scan:
                interfaces = _winreg.OpenKey(lm,
                                             r'SYSTEM\CurrentControlSet'
                                             r'\Services\Tcpip\Parameters'
                                             r'\Interfaces')
                try:
                    i = 0
                    while True:
                        try:
                            guid = _winreg.EnumKey(interfaces, i)
                            i += 1
                            key = _winreg.OpenKey(interfaces, guid)
                            try:
                                # enabled interfaces seem to have a non-empty
                                # NTEContextList
                                try:
                                    (nte, ttype) = _winreg.QueryValueEx(key,
                                                             'NTEContextList')
                                except WindowsError:
                                    nte = None
                                if nte:
                                    self._config_win32_fromkey(key)
                            finally:
                                key.Close()
                        except EnvironmentError:
                            break
                finally:
                    interfaces.Close()
        finally:
            lm.Close()

    def query(self, qname, rdtype=linkcheck.dns.rdatatype.A,
              rdclass=linkcheck.dns.rdataclass.IN, tcp=False):
        """Query nameservers to find the answer to the question.

        The I{qname}, I{rdtype}, and I{rdclass} parameters may be objects
        of the appropriate type, or strings that can be converted into objects
        of the appropriate type.  E.g. For I{rdtype} the integer 2 and the
        the string 'NS' both mean to query for records with DNS rdata type NS.

        @param qname: the query name
        @type qname: linkcheck.dns.name.Name object or string
        @param rdtype: the query type
        @type rdtype: int or string
        @param rdclass: the query class
        @type rdclass: int or string
        @param tcp: use TCP to make the query (default is False).
        @type tcp: bool
        @rtype: linkcheck.dns.resolver.Answer instance
        @raises Timeout: no answers could be found in the specified lifetime
        @raises NXDOMAIN: the query name does not exist
        @raises NoAnswer: the response did not contain an answer
        @raises NoNameservers: no non-broken nameservers are available to
        answer the question."""

        if isinstance(qname, str):
            qname = linkcheck.dns.name.from_text(qname, None)
        if isinstance(rdtype, str):
            rdtype = linkcheck.dns.rdatatype.from_text(rdtype)
        if isinstance(rdclass, str):
            rdclass = linkcheck.dns.rdataclass.from_text(rdclass)
        qnames_to_try = []
        if qname.is_absolute():
            qnames_to_try.append(qname)
        else:
            if len(qname) > 1:
                qnames_to_try.append(qname.concatenate(linkcheck.dns.name.root))
            if self.search:
                for suffix in self.search:
                    qnames_to_try.append(qname.concatenate(suffix))
            else:
                qnames_to_try.append(qname.concatenate(self.domain))
        all_nxdomain = True
        start = time.time()
        for qname in qnames_to_try:
            if self.cache:
                answer = self.cache.get((qname, rdtype, rdclass))
                if answer:
                    return answer
            request = linkcheck.dns.message.make_query(qname, rdtype, rdclass)
            if not self.keyname is None:
                request.use_tsig(self.keyring, self.keyname)
            request.use_edns(self.edns, self.ednsflags, self.payload)
            response = None
            #
            # make a copy of the servers list so we can alter it later.
            #
            nameservers = self.nameservers[:]
            while response is None:
                if len(nameservers) == 0:
                    raise NoNameservers("No DNS servers could answer the query")
                for nameserver in nameservers:
                    now = time.time()
                    if now < start:
                        # Time going backwards is bad.  Just give up.
                        raise Timeout("DNS query timed out")
                    duration = now - start
                    if duration >= self.lifetime:
                        raise Timeout("DNS query timed out")
                    timeout = min(self.lifetime - duration, self.timeout)
                    try:
                        if tcp:
                            response = linkcheck.dns.query.tcp(request, nameserver,
                                                     timeout, self.port)
                        else:
                            response = linkcheck.dns.query.udp(request, nameserver,
                                                     timeout, self.port)
                    except (socket.error, linkcheck.dns.exception.Timeout):
                        #
                        # Communication failure or timeout.  Go to the
                        # next server
                        #
                        response = None
                        continue
                    except linkcheck.dns.query.UnexpectedSource:
                        #
                        # Who knows?  Keep going.
                        #
                        response = None
                        continue
                    except linkcheck.dns.exception.FormError:
                        #
                        # We don't understand what this server is
                        # saying.  Take it out of the mix and
                        # continue.
                        #
                        nameservers.remove(nameserver)
                        response = None
                        continue
                    rcode = response.rcode()
                    if rcode == linkcheck.dns.rcode.NOERROR or \
                           rcode == linkcheck.dns.rcode.NXDOMAIN:
                        break
                    response = None
            if response.rcode() == linkcheck.dns.rcode.NXDOMAIN:
                continue
            all_nxdomain = False
            break
        if all_nxdomain:
            raise NXDOMAIN("Domain does not exist")
        answer = Answer(qname, rdtype, rdclass, response)
        if self.cache:
            self.cache.put((qname, rdtype, rdclass), answer)
        return answer

    def use_tsig(self, keyring, keyname=None):
        """Add a TSIG signature to the query.

        @param keyring: The TSIG keyring to use; defaults to None.
        @type keyring: dict
        @param keyname: The name of the TSIG key to use; defaults to None.
        The key must be defined in the keyring.  If a keyring is specified
        but a keyname is not, then the key used will be the first key in the
        keyring.  Note that the order of keys in a dictionary is not defined,
        so applications should supply a keyname when a keyring is used, unless
        they know the keyring contains only one key."""
        self.keyring = keyring
        if keyname is None:
            self.keyname = self.keyring.keys()[0]
        else:
            self.keyname = keyname

    def use_edns(self, edns, ednsflags, payload):
        """Configure Elinkcheck.dns.

        @param edns: The EDNS level to use.  The default is -1, no Elinkcheck.dns.
        @type edns: int
        @param ednsflags: The EDNS flags
        @type ednsflags: int
        @param payload: The EDNS payload size.  The default is 0.
        @type payload: int"""

        if edns is None:
            edns = -1
        self.edns = edns
        self.ednsflags = ednsflags
        self.payload = payload

default_resolver = None

def query(qname, rdtype=linkcheck.dns.rdatatype.A, rdclass=linkcheck.dns.rdataclass.IN,
          tcp=False):
    """Query nameservers to find the answer to the question.

    This is a convenience function that uses the default resolver
    object to make the query.
    @see: L{linkcheck.dns.resolver.Resolver.query} for more information on the
    parameters."""
    global default_resolver
    if default_resolver is None:
        default_resolver = Resolver()
    return default_resolver.query(qname, rdtype, rdclass, tcp)
