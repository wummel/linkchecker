# -*- coding: iso-8859-1 -*-
"""from http://twistedmatrix.com/wiki/python/IfConfig
"""
import socket
import errno
import array
import struct
from _network import ifreq_size
from .. import log, LOG_DNS


class IfConfig (object):
    """Access to socket interfaces"""

    SIOCGIFNAME = 0x8910
    SIOCGIFCONF = 0x8912
    SIOCGIFFLAGS = 0x8913
    SIOCGIFADDR = 0x8915
    SIOCGIFBRDADDR = 0x8919
    SIOCGIFNETMASK = 0x891b
    SIOCGIFCOUNT = 0x8938

    IFF_UP = 0x1                # Interface is up.
    IFF_BROADCAST = 0x2         # Broadcast address valid.
    IFF_DEBUG = 0x4             # Turn on debugging.
    IFF_LOOPBACK = 0x8          # Is a loopback net.
    IFF_POINTOPOINT = 0x10      # Interface is point-to-point link.
    IFF_NOTRAILERS = 0x20       # Avoid use of trailers.
    IFF_RUNNING = 0x40          # Resources allocated.
    IFF_NOARP = 0x80            # No address resolution protocol.
    IFF_PROMISC = 0x100         # Receive all packets.
    IFF_ALLMULTI = 0x200        # Receive all multicast packets.
    IFF_MASTER = 0x400          # Master of a load balancer.
    IFF_SLAVE = 0x800           # Slave of a load balancer.
    IFF_MULTICAST = 0x1000      # Supports multicast.
    IFF_PORTSEL = 0x2000        # Can set media type.
    IFF_AUTOMEDIA = 0x4000      # Auto media select active.

    def __init__ (self):
        # create a socket so we have a handle to query
        self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Note that sizeof(struct ifreq) is not always 32
        # (eg. on *BSD, x86_64 Linux) Thus the function call.
        self.ifr_size = ifreq_size()

    def _ioctl (self, func, args):
        import fcntl
        return fcntl.ioctl(self.sockfd.fileno(), func, args)

    def _getifreq (self, ifname):
        """Return ifreq buffer for given interface name."""
        return struct.pack("%ds" % self.ifr_size, ifname)

    def _getaddr (self, ifname, func):
        try:
            result = self._ioctl(func, self._getifreq(ifname))
        except IOError, msg:
            log.warn(LOG_DNS,
                  "error getting addr for interface %r: %s", ifname, msg)
            return None
        return socket.inet_ntoa(result[20:24])

    def getInterfaceList (self):
        """Get all interface names in a list."""
        # initial 8kB buffer to hold interface data
        bufsize = 8192
        # 80kB buffer should be enough for most boxen
        max_bufsize = bufsize * 10
        while True:
            buf = array.array('c', '\0' * bufsize)
            ifreq = struct.pack("iP", buf.buffer_info()[1], buf.buffer_info()[0])
            try:
                result = self._ioctl(self.SIOCGIFCONF, ifreq)
                break
            except IOError, msg:
                # in case of EINVAL the buffer size was too small
                if msg[0] != errno.EINVAL or bufsize == max_bufsize:
                    raise
            # increase buffer
            bufsize += 8192
        # loop over interface names
        data = buf.tostring()
        iflist = []
        size, ptr = struct.unpack("iP", result)
        i = 0
        while i < size:
            ifconf = data[i:i+self.ifr_size]
            name = struct.unpack("16s%ds" % (self.ifr_size-16), ifconf)[0]
            name = name.split('\0', 1)[0]
            if name:
                iflist.append(name)
            i += self.ifr_size
        return iflist

    def getFlags (self, ifname):
        """Get the flags for an interface"""
        try:
            result = self._ioctl(self.SIOCGIFFLAGS, self._getifreq(ifname))
        except IOError, msg:
            log.warn(LOG_DNS,
                 "error getting flags for interface %r: %s", ifname, msg)
            return 0
        # extract the interface's flags from the return value
        flags, = struct.unpack('H', result[16:18])
        # return "UP" bit
        return flags

    def getAddr (self, ifname):
        """Get the inet addr for an interface.
        @param ifname: interface name
        @type ifname: string
        """
        return self._getaddr(ifname, self.SIOCGIFADDR)

    def getMask (self, ifname):
        """Get the netmask for an interface.
        @param ifname: interface name
        @type ifname: string
        """
        return self._getaddr(ifname, self.SIOCGIFNETMASK)

    def getBroadcast (self, ifname):
        """Get the broadcast addr for an interface.
        @param ifname: interface name
        @type ifname: string
        """
        return self._getaddr(ifname, self.SIOCGIFBRDADDR)

    def isUp (self, ifname):
        """Check whether interface is UP.
        @param ifname: interface name
        @type ifname: string
        """
        return (self.getFlags(ifname) & self.IFF_UP) != 0

    def isLoopback (self, ifname):
        """Check whether interface is a loopback device.
        @param ifname: interface name
        @type ifname: string
        """
        # since not all systems have IFF_LOOPBACK as a flag defined,
        # the ifname is tested first
        if ifname == 'lo':
            return True
        return (self.getFlags(ifname) & self.IFF_LOOPBACK) != 0
