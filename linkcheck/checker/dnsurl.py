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
Handle for dns: links.
"""

import socket

from . import urlbase


class DnsUrl (urlbase.UrlBase):
    """
    Url link with dns scheme.
    """

    def can_get_content (self):
        """
        dns: URLs do not have any content

        @return: False
        @rtype: bool
        """
        return False

    def check_connection(self):
        """Resolve hostname."""
        host = self.urlparts[1]
        addresses = socket.getaddrinfo(host, 80, 0, 0, socket.SOL_TCP)
        args = {'host': host}
        if addresses:
            args['ips'] = [x[4][0] for x in addresses]
            self.set_result(_('%(host)s resolved to IPs %(ips)s') % args, valid=True)
        else:
            self.set_result(_('%(host)r could not be resolved') % args, valid=False)
