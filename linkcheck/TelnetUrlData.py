"""Handle telnet: links"""
#    Copyright (C) 2000,2001  Bastian Kleineidam
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import telnetlib,re,string,linkcheck
from HostCheckingUrlData import HostCheckingUrlData
from linkcheck import _

# regular expression for syntax checking
telnet_re =  re.compile("^telnet:[\w.\-]+$")

class TelnetUrlData(HostCheckingUrlData):
    "Url link with telnet scheme"

    def buildUrl(self):
        HostCheckingUrlData.buildUrl(self)
        if not telnet_re.match(self.urlName):
            raise linkcheck.error, _("Illegal telnet link syntax")
        self.host = string.lower(self.urlName[7:])

    def get_scheme(self):
        return "telnet"

    def checkConnection(self, config):
        HostCheckingUrlData.checkConnection(self, config)
        self.urlConnection = telnetlib.Telnet()
        self.urlConnection.open(self.host, 23)
