# -*- coding: iso-8859-1 -*-
""" ip related utility functions """
# Copyright (C) 2003-2004  Bastian Kleineidam
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

import re
import socket
import struct
import math
import sets
import bk.log


# IP Adress regular expressions
_ipv4_num = r"\d{1,3}"
_ipv4_num_4 = r"%s\.%s\.%s\.%s" % ((_ipv4_num,)*4)
_ipv4_re = re.compile(r"^%s$" % _ipv4_num_4)
# see rfc2373
_ipv6_num = r"[\da-f]{1,4}"
_ipv6_re = re.compile(r"^%s:%s:%s:%s:%s:%s:%s:%s$" % ((_ipv6_num,)*8))
_ipv6_ipv4_re = re.compile(r"^%s:%s:%s:%s:%s:%s:" % ((_ipv6_num,)*6) + \
                           r"%s$" % _ipv4_num_4)
_ipv6_abbr_re = re.compile(r"^((%s:){0,6}%s)?::((%s:){0,6}%s)?$" % \
                            ((_ipv6_num,)*4))
_ipv6_ipv4_abbr_re = re.compile(r"^((%s:){0,4}%s)?::((%s:){0,5})?" % \
                           ((_ipv6_num,)*3) + \
                           "%s$" % _ipv4_num_4)
# netmask regex
_host_netmask_re = re.compile(r"^%s/%s$" % (_ipv4_num_4, _ipv4_num_4))
_host_bitmask_re = re.compile(r"^%s/\d{1,2}$" % _ipv4_num_4)


def expand_ipv6 (ip, num):
    """expand an IPv6 address with included :: to num octets
       raise ValueError on invalid IP addresses
    """
    i = ip.find("::")
    prefix = ip[:i]
    suffix = ip[i+2:]
    count = prefix.count(":") + suffix.count(":")
    if prefix:
        count += 1
        prefix = prefix+":"
    if suffix:
        count += 1
        suffix = ":"+suffix
    if count>=num: raise ValueError("invalid ipv6 number: %s"%ip)
    fill = (num-count-1)*"0:" + "0"
    return prefix+fill+suffix


def expand_ip (ip):
    """ipv6 addresses are expanded to full 8 octets, all other
       addresses are left untouched
       return a tuple (ip, num) where num==1 if ip is a numeric ip, 0
       otherwise.
    """
    if _ipv4_re.match(ip) or \
       _ipv6_re.match(ip) or \
       _ipv6_ipv4_re.match(ip):
        return (ip, 1)
    if _ipv6_abbr_re.match(ip):
        return (expand_ipv6(ip, 8), 1)
    if _ipv6_ipv4_abbr_re.match(ip):
        i = ip.rfind(":") + 1
        return (expand_ipv6(ip[:i], 6) + ip[i:], 1)
    return (ip, 0)


def is_valid_ip (ip):
    """Return True if given ip is a valid IPv4 or IPv6 address"""
    return is_valid_ipv4(ip) or is_valid_ipv6(ip)


def is_valid_ipv4 (ip):
    """Return True if given ip is a valid IPv4 address"""
    if not _ipv4_re.match(ip):
        return False
    a,b,c,d = [int(i) for i in ip.split(".")]
    return a<=255 and b<=255 and c<=255 and d<=255


def is_valid_ipv6 (ip):
    """Return True if given ip is a valid IPv6 address"""
    # XXX this is not complete: check ipv6 and ipv4 semantics too here
    if not (_ipv6_re.match(ip) or _ipv6_ipv4_re.match(ip) or
            _ipv6_abbr_re.match(ip) or _ipv6_ipv4_abbr_re.match(ip)):
        return False
    return True


def is_valid_bitmask (mask):
    """Return True if given mask is a valid network bitmask"""
    return 1<=mask<=32


def dq2num (ip):
    "convert decimal dotted quad string to long integer"
    return struct.unpack('!L', socket.inet_aton(ip))[0]


def num2dq (n):
    "convert long int to dotted quad string"
    return socket.inet_ntoa(struct.pack('!L', n))


def suffix2mask (n):
    "return a mask of n bits as a long integer"
    return (1L << (32 - n)) - 1


def mask2suffix (mask):
    """return suff for given bit mask"""
    return 32 - int(math.log(mask+1, 2))


def dq2mask (ip):
    "return a mask of bits as a long integer"
    n = dq2num(ip)
    return -((-n+1) | n)


def dq2net (ip, mask):
    "return a tuple (network ip, network mask) for given ip and mask"
    n = dq2num(ip)
    net = n - (n & mask)
    return (net, mask)


def dq_in_net (n, net, mask):
    """return True iff numerical ip n is in given net with mask.
       (net,mask) must be returned previously by ip2net"""
    m = n - (n & mask)
    return m==net


def host_in_set (ip, hosts, nets):
    """return True if given ip is in host or network list"""
    if ip in hosts:
        return True
    if is_valid_ipv4(ip):
        n = dq2num(ip)
        for net, mask in nets:
            if dq_in_net(n, net, mask):
                return True
    return False


def strhosts2map (strhosts):
    """convert a string representation of hosts and networks to
       a tuple (hosts, networks)"""
    return hosts2map([s.strip() for s in strhosts.split(",") if s])


def hosts2map (hosts):
    """return a set of named hosts, and a list of subnets (host/netmask
       adresses).
       Only IPv4 host/netmasks are supported.
    """
    hostset = sets.Set()
    nets = []
    for host in hosts:
        if _host_bitmask_re.match(host):
            host, mask = host.split("/")
            mask = int(mask)
            if not is_valid_bitmask(mask):
                bk.log.error(bk.LOG_NET,
                             "bitmask %d is not a valid network mask", mask)
                continue
            if not is_valid_ipv4(host):
                bk.log.error(bk.LOG_NET,
                             "host %r is not a valid ip address", host)
                continue
            nets.append(dq2net(host, suffix2mask(mask)))
        elif _host_netmask_re.match(host):
            host, mask = host.split("/")
            if not is_valid_ipv4(host):
                bk.log.error(bk.LOG_NET,
                             "host %r is not a valid ip address", host)
                continue
            if not is_valid_ipv4(mask):
                bk.log.error(bk.LOG_NET,
                             "mask %r is not a valid ip network mask", mask)
                continue
            nets.append(dq2net(host, dq2mask(mask)))
        elif is_valid_ip(host):
            hostset.add(expand_ip(host)[0])
        else:
            try:
                hostset |= resolve_host(host)
            except socket.gaierror:
                bk.log.error(bk.LOG_NET, "invalid host %r", host)
    return (hostset, nets)


def map2hosts (hostmap):
    """convert a tuple (hosts, networks) into a host/network list
       suitable for storing in a config file"""
    ret = hostmap[0].copy()
    for net, mask in hostmap[1]:
        ret.add("%s/%d" % (num2dq(net), mask2suffix(mask)))
    return ret


def lookup_ips (ips):
    """return set of host names that resolve to given ips"""
    hosts = sets.Set()
    for ip in ips:
        try:
            hosts.add(socket.gethostbyaddr(ip)[0])
        except socket.error:
            hosts.add(ip)
    return hosts


def resolve_host (host):
    """return set of ip numbers for given host"""
    ips = sets.Set()
    for res in socket.getaddrinfo(host, None, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        ips.add(sa[0])
    return ips

