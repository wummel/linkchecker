# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Check page content for virus infection with clamav.
"""
import os
import socket
from . import _ContentPlugin
from .. import log, LOG_PLUGIN
from ..socketutil import create_socket


class VirusCheck(_ContentPlugin):
    """Checks the page content for virus infections with clamav.
    A local clamav daemon must be installed."""

    def __init__(self, config):
        """Initialize clamav configuration."""
        super(VirusCheck, self).__init__(config)
        # XXX read config
        self.clamav_conf = get_clamav_conf(canonical_clamav_conf())
        if not self.clamav_conf:
            log.warn(LOG_PLUGIN, "clamav daemon not found for VirusCheck plugin")

    def applies_to(self, url_data):
        """Check for clamav and extern."""
        return self.clamav_conf and not url_data.extern[0]

    def check(self, url_data):
        """Try to ask GeoIP database for country info."""
        data = url_data.get_content()
        infected, errors = scan(data, self.clamav_conf)
        if infected or errors:
            for msg in infected:
                url_data.add_warning(u"Virus scan infection: %s" % msg)
            for msg in errors:
                url_data.add_warning(u"Virus scan error: %s" % msg)
        else:
            url_data.add_info("No viruses in data found.")

    @classmethod
    def read_config(cls, configparser):
        """Read configuration file options."""
        config = dict()
        section = cls.__name__
        option = "clamavconf"
        if configparser.has_option(section, option):
            value = configparser.get(section, option)
        else:
            value = None
        config[option] = value
        return config


class ClamavError (Exception):
    """Raised on clamav errors."""
    pass


class ClamdScanner (object):
    """Virus scanner using a clamd daemon process."""

    def __init__ (self, clamav_conf):
        """Initialize clamd daemon process sockets."""
        self.infected = []
        self.errors = []
        self.sock, self.host = clamav_conf.new_connection()
        self.sock_rcvbuf = \
             self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        self.wsock = self.new_scansock()

    def new_scansock (self):
        """Return a connected socket for sending scan data to it."""
        port = None
        try:
            self.sock.sendall("STREAM")
            port = None
            for dummy in range(60):
                data = self.sock.recv(self.sock_rcvbuf)
                i = data.find("PORT")
                if i != -1:
                    port = int(data[i+5:])
                    break
        except socket.error:
            self.sock.close()
            raise
        if port is None:
            raise ClamavError(_("clamd is not ready for stream scanning"))
        sockinfo = get_sockinfo(self.host, port=port)
        wsock = create_socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            wsock.connect(sockinfo[0][4])
        except socket.error:
            wsock.close()
            raise
        return wsock

    def scan (self, data):
        """Scan given data for viruses."""
        self.wsock.sendall(data)

    def close (self):
        """Get results and close clamd daemon sockets."""
        self.wsock.close()
        data = self.sock.recv(self.sock_rcvbuf)
        while data:
            if "FOUND\n" in data:
                self.infected.append(data)
            if "ERROR\n" in data:
                self.errors.append(data)
            data = self.sock.recv(self.sock_rcvbuf)
        self.sock.close()


def canonical_clamav_conf ():
    """Default clamav configs for various platforms."""
    if os.name == 'posix':
        clamavconf = "/etc/clamav/clamd.conf"
    elif os.name == 'nt':
        clamavconf = r"c:\clamav-devel\etc\clamd.conf"
    else:
        clamavconf = "clamd.conf"
    return clamavconf


def get_clamav_conf(filename):
    """Initialize clamav configuration."""
    if os.path.isfile(filename):
        return ClamavConfig(filename)
    log.warn(LOG_PLUGIN, "No ClamAV config file found at %r.", filename)


def get_sockinfo (host, port=None):
    """Return socket.getaddrinfo for given host and port."""
    family, socktype = socket.AF_INET, socket.SOCK_STREAM
    return socket.getaddrinfo(host, port, family, socktype)


class ClamavConfig (dict):
    """Clamav configuration wrapper, with clamd connection method."""

    def __init__ (self, filename):
        """Parse clamav configuration file."""
        super(ClamavConfig, self).__init__()
        self.parseconf(filename)
        if self.get('ScannerDaemonOutputFormat'):
            raise ClamavError(_("ScannerDaemonOutputFormat must be disabled"))
        if self.get('TCPSocket') and self.get('LocalSocket'):
            raise ClamavError(_("only one of TCPSocket and LocalSocket must be enabled"))

    def parseconf (self, filename):
        """Parse clamav configuration from given file."""
        with open(filename) as fd:
            # yet another config format, sigh
            for line in fd:
                line = line.strip()
                if not line or line.startswith("#"):
                    # ignore empty lines and comments
                    continue
                split = line.split(None, 1)
                if len(split) == 1:
                    self[split[0]] = True
                else:
                    self[split[0]] = split[1]

    def new_connection (self):
        """Connect to clamd for stream scanning.

        @return: tuple (connected socket, host)
        """
        if self.get('LocalSocket'):
            host = 'localhost'
            sock = self.create_local_socket()
        elif self.get('TCPSocket'):
            host = self.get('TCPAddr', 'localhost')
            sock = self.create_tcp_socket(host)
        else:
            raise ClamavError(_("one of TCPSocket or LocalSocket must be enabled"))
        return sock, host

    def create_local_socket (self):
        """Create local socket, connect to it and return socket object."""
        sock = create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
        addr = self['LocalSocket']
        try:
            sock.connect(addr)
        except socket.error:
            sock.close()
            raise
        return sock

    def create_tcp_socket (self, host):
        """Create tcp socket, connect to it and return socket object."""
        port = int(self['TCPSocket'])
        sockinfo = get_sockinfo(host, port=port)
        sock = create_socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(sockinfo[0][4])
        except socket.error:
            sock.close()
            raise
        return sock


def scan (data, clamconf):
    """Scan data for viruses.
    @return (infection msgs, errors)
    @rtype ([], [])
    """
    try:
        scanner = ClamdScanner(clamconf)
    except socket.error:
        errmsg = _("Could not connect to ClamAV daemon.")
        return ([], [errmsg])
    try:
        scanner.scan(data)
    finally:
        scanner.close()
    return scanner.infected, scanner.errors
