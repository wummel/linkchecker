# -*- coding: iso-8859-1 -*-
"""network utilities"""
# Copyright (C) 2004  Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


import os
import sets
import socket
import bk.log
import bk.containers
if os.name=='posix':
    import posix as platform_net
elif os.name=='nt':
    import nt as platform_net
else:
    platform_net = None

LOG_NET = "bk.net"


def get_localhosts ():
    """get list of localhost names and ips"""
    # XXX is this default list of localhost stuff complete?
    localhosts = sets.Set([
      'localhost',
      'loopback',
      '127.0.0.1',
      '::1',
      'ip6-localhost',
      'ip6-loopback',
    ])
    add_addrinfo(localhosts, socket.gethostname())
    # add system specific hosts for all interfaces
    if platform_net is not None:
        for addr in platform_net.get_localaddrs():
            add_addrinfo(localhosts, addr)
    else:
        bk.log.warn(LOG_NET, "platform %r network not supported", os.name)
    return localhosts


def add_addrinfo (hosts, host):
    try:
        addrinfo = socket.gethostbyaddr(host)
    except socket.error:
        hosts.add(host.lower())
        return
    hosts.add(addrinfo[0].lower())
    for h in addrinfo[1]:
        hosts.add(h.lower())
    for h in addrinfo[2]:
        hosts.add(h.lower())


class DnsConfig (object):
    """DNS configuration storage"""
    def __init__ (self):
        self.nameservers = bk.containers.SetList()
        self.search_domains = bk.containers.SetList()
        self.search_patterns = ('www.%s.com', 'www.%s.net', 'www.%s.org')

    def __str__ (self):
        return "nameservers: "+str(self.nameservers)+\
               "\nsearch domains: "+str(self.search_domains)+\
               "\nsearch_patterns: "+str(self.search_patterns)


def resolver_config ():
    """dns resolver configuration"""
    config = DnsConfig()
    if platform_net is not None:
        platform_net.resolver_config(config)
    else:
        bk.log.warn(LOG_NET, "platform %r network not supported", os.name)
    if not config.search_domains:
        config.search_domains.append('')
    if not config.nameservers:
        config.nameservers.append('127.0.0.1')
    bk.log.debug(LOG_NET, "nameservers %s", config.nameservers)
    bk.log.debug(LOG_NET, "search domains %s", config.search_domains)
    return config


if __name__=='__main__':
    print "localhosts:", get_localhosts()
    print resolver_config()
