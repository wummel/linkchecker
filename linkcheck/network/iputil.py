# -*- coding: iso-8859-1 -*-
# Copyright (C) 2003-2014 Bastian Kleineidam
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
Ip number related utility functions.
"""

import re
import socket
import struct
from .. import log, LOG_CHECK


# IP Adress regular expressions
# Note that each IPv4 octet can be encoded in dezimal, hexadezimal and octal.
_ipv4_num = r"\d{1,3}"
_ipv4_hex = r"0*[\da-f]{1,2}"
_ipv4_oct = r"0+[0-7]{0, 3}"
# XXX
_ipv4_num_4 = r"%s\.%s\.%s\.%s" % ((_ipv4_num,) * 4)
_ipv4_re = re.compile(r"^%s$" % _ipv4_num_4)
_ipv4_hex_4 = r"%s\.%s\.%s\.%s" % ((_ipv4_hex,) * 4)
# IPv4 encoded in octal, eg. 0x42.0x66.0x0d.0x63
_ipv4_oct = r"0*[0-7]{1,3}"
_ipv4_hex_4 = r"%s\.%s\.%s\.%s" % ((_ipv4_hex,) * 4)


# IPv6; See also rfc2373
_ipv6_num = r"[\da-f]{1,4}"
_ipv6_re = re.compile(r"^%s:%s:%s:%s:%s:%s:%s:%s$" % ((_ipv6_num,) * 8))
_ipv6_ipv4_re = re.compile(r"^%s:%s:%s:%s:%s:%s:" % ((_ipv6_num,) * 6) + \
                           r"%s$" % _ipv4_num_4)
_ipv6_abbr_re = re.compile(r"^((%s:){0,6}%s)?::((%s:){0,6}%s)?$" % \
                            ((_ipv6_num,) * 4))
_ipv6_ipv4_abbr_re = re.compile(r"^((%s:){0,4}%s)?::((%s:){0,5})?" % \
                           ((_ipv6_num,) * 3) + \
                           "%s$" % _ipv4_num_4)
# netmask regex
_host_netmask_re = re.compile(r"^%s/%s$" % (_ipv4_num_4, _ipv4_num_4))
_host_cidrmask_re = re.compile(r"^%s/\d{1,2}$" % _ipv4_num_4)


def expand_ipv6 (ip, num):
    """
    Expand an IPv6 address with included :: to num octets.

    @raise: ValueError on invalid IP addresses
    """
    i = ip.find("::")
    prefix = ip[:i]
    suffix = ip[i + 2:]
    count = prefix.count(":") + suffix.count(":")
    if prefix:
        count += 1
        prefix = prefix + ":"
    if suffix:
        count += 1
        suffix = ":" + suffix
    if count >= num:
        raise ValueError("invalid ipv6 number: %s" % ip)
    fill = (num - count - 1) * "0:" + "0"
    return prefix + fill + suffix


def expand_ip (ip):
    """
    ipv6 addresses are expanded to full 8 octets, all other
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
    """
    Return True if given ip is a valid IPv4 or IPv6 address.
    """
    return is_valid_ipv4(ip) or is_valid_ipv6(ip)


def is_valid_ipv4 (ip):
    """
    Return True if given ip is a valid IPv4 address.
    """
    if not _ipv4_re.match(ip):
        return False
    a, b, c, d = [int(i) for i in ip.split(".")]
    return a <= 255 and b <= 255 and c <= 255 and d <= 255


def is_valid_ipv6 (ip):
    """
    Return True if given ip is a valid IPv6 address.
    """
    # XXX this is not complete: check ipv6 and ipv4 semantics too here
    if not (_ipv6_re.match(ip) or _ipv6_ipv4_re.match(ip) or
            _ipv6_abbr_re.match(ip) or _ipv6_ipv4_abbr_re.match(ip)):
        return False
    return True


def is_valid_cidrmask (mask):
    """
    Check if given mask is a valid network bitmask in CIDR notation.
    """
    return 0 <= mask <= 32


def dq2num (ip):
    """
    Convert decimal dotted quad string to long integer.
    """
    return struct.unpack('!L', socket.inet_aton(ip))[0]


def num2dq (n):
    """
    Convert long int to dotted quad string.
    """
    return socket.inet_ntoa(struct.pack('!L', n))


def cidr2mask (n):
    """
    Return a mask where the n left-most of 32 bits are set.
    """
    return ((1 << n) - 1) << (32 - n)


def netmask2mask (ip):
    """
    Return a mask of bits as a long integer.
    """
    return dq2num(ip)


def mask2netmask (mask):
    """
    Return dotted quad string as netmask.
    """
    return num2dq(mask)


def dq2net (ip, mask):
    """
    Return a tuple (network ip, network mask) for given ip and mask.
    """
    return dq2num(ip) & mask


def dq_in_net (n, mask):
    """
    Return True iff numerical ip n is in given network.
    """
    return (n & mask) == mask


def host_in_set (ip, hosts, nets):
    """
    Return True if given ip is in host or network list.
    """
    if ip in hosts:
        return True
    if is_valid_ipv4(ip):
        n = dq2num(ip)
        for net in nets:
            if dq_in_net(n, net):
                return True
    return False


def strhosts2map (strhosts):
    """
    Convert a string representation of hosts and networks to
    a tuple (hosts, networks).
    """
    return hosts2map([s.strip() for s in strhosts.split(",") if s])


def hosts2map (hosts):
    """
    Return a set of named hosts, and a list of subnets (host/netmask
    adresses).
    Only IPv4 host/netmasks are supported.
    """
    hostset = set()
    nets = []
    for host in hosts:
        if _host_cidrmask_re.match(host):
            host, mask = host.split("/")
            mask = int(mask)
            if not is_valid_cidrmask(mask):
                log.error(LOG_CHECK,
                          "CIDR mask %d is not a valid network mask", mask)
                continue
            if not is_valid_ipv4(host):
                log.error(LOG_CHECK, "host %r is not a valid ip address", host)
                continue
            nets.append(dq2net(host, cidr2mask(mask)))
        elif _host_netmask_re.match(host):
            host, mask = host.split("/")
            if not is_valid_ipv4(host):
                log.error(LOG_CHECK, "host %r is not a valid ip address", host)
                continue
            if not is_valid_ipv4(mask):
                log.error(LOG_CHECK,
                          "mask %r is not a valid ip network mask", mask)
                continue
            nets.append(dq2net(host, netmask2mask(mask)))
        elif is_valid_ip(host):
            hostset.add(expand_ip(host)[0])
        else:
            hostset |= set(resolve_host(host))
    return (hostset, nets)


def map2hosts (hostmap):
    """
    Convert a tuple (hosts, networks) into a host/network list
    suitable for storing in a config file.
    """
    ret = hostmap[0].copy()
    for net, mask in hostmap[1]:
        ret.add("%s/%d" % (num2dq(net), mask2netmask(mask)))
    return ret


def lookup_ips (ips):
    """
    Return set of host names that resolve to given ips.
    """
    hosts = set()
    for ip in ips:
        try:
            hosts.add(socket.gethostbyaddr(ip)[0])
        except socket.error:
            hosts.add(ip)
    return hosts


def resolve_host (host):
    """
    @host: hostname or IP address
    Return list of ip numbers for given host.
    """
    ips = []
    try:
        for res in socket.getaddrinfo(host, None, 0, socket.SOCK_STREAM):
            # res is a tuple (address family, socket type, protocol,
            #  canonical name, socket address)
            # add first ip of socket address
            ips.append(res[4][0])
    except socket.error:
        log.info(LOG_CHECK, "Ignored invalid host %r", host)
    return ips


def obfuscate_ip(ip):
    """Obfuscate given host in IP form.
    @ip: IPv4 address string
    @return: hexadecimal IP string ('0x1ab...')
    @raise: ValueError on invalid IP addresses
    """
    if is_valid_ipv4(ip):
        res = "0x%s" % "".join(hex(int(x))[2:] for x in ip.split("."))
    else:
        raise ValueError('Invalid IP value %r' % ip)
    assert is_obfuscated_ip(res),  '%r obfuscation error' % res
    return res


is_obfuscated_ip = re.compile(r"^(0x[a-f0-9]+|[0-9]+)$").match
