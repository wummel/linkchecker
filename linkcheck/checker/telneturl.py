# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2005  Bastian Kleineidam
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
"""
Handle telnet: links.
"""

import telnetlib
import urlparse
import urllib

import linkcheck
import urlbase


class TelnetUrl (urlbase.UrlBase):
    """
    Url link with telnet scheme.
    """

    def build_url (self):
        super(TelnetUrl, self).build_url()
        # default port
        if self.port is None:
            self.port = 23
        # split user/pass
        if self.userinfo:
            self.user, self.password = urllib.splitpasswd(self.userinfo)
        else:
            self.user, self.password = self.get_user_password()

    def local_check (self):
        if not self.host:
            self.set_result(_("Host is empty"), valid=False)
            return
        super(TelnetUrl, self).local_check()

    def check_connection (self):
        self.url_connection = telnetlib.Telnet()
        if self.consumer.config.get("debug"):
            self.url_connection.set_debuglevel(1)
        self.url_connection.open(self.host, self.port)
        if self.user:
            self.url_connection.read_until("login: ", 10)
            self.url_connection.write(self.user+"\n")
            if self.password:
                self.url_connection.read_until("Password: ", 10)
                self.url_connection.write(self.password+"\n")
                # XXX how to tell if we are logged in??
        self.url_connection.write("exit\n")

    def can_get_content (self):
        return False
