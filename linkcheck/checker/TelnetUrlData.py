# -*- coding: iso-8859-1 -*-
"""Handle telnet: links"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

import telnetlib
import urlparse
import urllib
import linkcheck


class TelnetUrlData (linkcheck.checker.HostCheckingUrlData.HostCheckingUrlData):
    "Url link with telnet scheme"

    def buildUrl (self):
        super(TelnetUrlData, self).buildUrl()
        parts = urlparse.urlsplit(self.url)
        userinfo, self.host = urllib.splituser(parts[1])
        self.host, self.port = urllib.splitport(self.host)
        if self.port is not None:
            if not linkcheck.UrlData.is_valid_port(self.port):
                raise linkcheck.LinkCheckerError(bk.i18n._("URL has invalid port number %s")\
                                      % self.port)
            self.port = int(self.port)
        else:
            self.port = 23
        if userinfo:
            self.user, self.password = urllib.splitpasswd(userinfo)
        else:
            self.user, self.password = self.getUserPassword()


    def checkConnection (self):
        super(TelnetUrlData, self).checkConnection()
        self.urlConnection = telnetlib.Telnet()
        self.urlConnection.set_debuglevel(get_debuglevel())
        self.urlConnection.open(self.host, self.port)
        if self.user:
            self.urlConnection.read_until("login: ", 10)
            self.urlConnection.write(self.user+"\n")
            if self.password:
                self.urlConnection.read_until("Password: ", 10)
                self.urlConnection.write(self.password+"\n")
                # XXX how to tell if we are logged in??
        self.urlConnection.write("exit\n")


    def hasContent (self):
        return False

