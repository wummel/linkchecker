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
Handle telnet: links.
"""

import telnetlib
from . import urlbase
from .. import log, LOG_CHECK


def encode(s, encoding="iso-8859-1", errors="ignore"):
    """Encode telnet data like username and password."""
    return s.encode(encoding, errors)


class TelnetUrl (urlbase.UrlBase):
    """
    Url link with telnet scheme.
    """

    def build_url (self):
        """
        Call super.build_url(), set default telnet port and initialize
        the login credentials.
        """
        super(TelnetUrl, self).build_url()
        # default port
        if self.port is None:
            self.port = 23
        # set user/pass
        self.user, self.password = self.get_user_password()

    def local_check (self):
        """
        Warn about empty host names. Else call super.local_check().
        """
        if not self.host:
            self.set_result(_("Host is empty"), valid=False)
            return
        super(TelnetUrl, self).local_check()

    def check_connection (self):
        """
        Open a telnet connection and try to login. Expected login
        label is "login: ", expected password label is "Password: ".
        """
        self.url_connection = telnetlib.Telnet(timeout=self.aggregate.config["timeout"])
        if log.is_debug(LOG_CHECK):
            self.url_connection.set_debuglevel(1)
        self.url_connection.open(self.host, self.port)
        if self.user:
            self.url_connection.read_until("login: ", 10)
            self.url_connection.write(encode(self.user)+"\n")
            if self.password:
                self.url_connection.read_until("Password: ", 10)
                self.url_connection.write(encode(self.password)+"\n")
                # XXX how to tell if we are logged in??
        self.url_connection.write("exit\n")

    def can_get_content (self):
        """
        Telnet URLs have no content.

        @return: False
        @rtype: bool
        """
        return False
