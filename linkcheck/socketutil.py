# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008-2014 Bastian Kleineidam
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

import socket


# test for IPv6, both in Python build and in kernel build
has_ipv6 = False
if socket.has_ipv6:
    # python has ipv6 compiled in, but the operating system also
    # has to support it.
    try:
        socket.socket(socket.AF_INET6, socket.SOCK_STREAM).close()
        has_ipv6 = True
    except socket.error as msg:
        # only catch these one:
        # socket.error: (97, 'Address family not supported by protocol')
        # socket.error: (10047, 'Address family not supported by protocol')
        # socket.error: (43, 'Protocol not supported')
        if msg.args[0] not in (97, 10047, 43):
            raise


def create_socket (family, socktype, proto=0, timeout=60):
    """
    Create a socket with given family and type. If SSL context
    is given an SSL socket is created.
    """
    sock = socket.socket(family, socktype, proto=proto)
    sock.settimeout(timeout)
    socktypes_inet = [socket.AF_INET]
    if has_ipv6:
        socktypes_inet.append(socket.AF_INET6)
    if family in socktypes_inet and socktype == socket.SOCK_STREAM:
        # disable NAGLE algorithm, which means sending pending data
        # immediately, possibly wasting bandwidth but improving
        # responsiveness for fast networks
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return sock
