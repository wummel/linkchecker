"""Handle telnet: links"""
# Copyright (C) 2000,2001  Bastian Kleineidam
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

import telnetlib, re, linkcheck
from HostCheckingUrlData import HostCheckingUrlData

# regular expression for syntax checking

_user = "[-a-zA-Z0-9$_.+!*'()]+"
_password = _user
_userpassword = r"((?P<user1>%s)|(?P<user>%s):(?P<password>%s))@" % \
                (_user, _user, _password)
_label = r"[a-zA-Z][-a-zA-Z0-9]*"
_host = r"%s(\.%s)*| " % (_label, _label)
_port = r"\d+"
telnet_re =  re.compile(r"^telnet://(%s)?(?P<host>%s)(:(?P<port>%s))?(/)?$"%\
                        (_userpassword, _host, _port))

class TelnetUrlData (HostCheckingUrlData):
    "Url link with telnet scheme"

    def buildUrl (self):
        HostCheckingUrlData.buildUrl(self)
        mo = telnet_re.match(self.urlName)
        if not mo:
            raise linkcheck.error, linkcheck._("Illegal telnet link syntax")
        self.user = mo.group("user")
        self.password = mo.group("password")
        self.host = mo.group("host")
        self.port = mo.group("port")
        if not self.port:
            self.port = 23

    def checkConnection (self):
        HostCheckingUrlData.checkConnection(self)
        self.urlConnection = telnetlib.Telnet()
        self.urlConnection.open(self.host, self.port)
        if self.user:
            self.urlConnection.read_until("login: ", 10)
            self.urlConnection.write(self.user+"\n")
            if self.password:
                self.urlConnection.read_until("Password: ", 10)
                self.urlConnection.write(self.password+"\n")
        self.urlConnection.write("exit\n")
