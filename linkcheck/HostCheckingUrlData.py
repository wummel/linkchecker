"""Base handle for links with a hostname"""
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

import socket,string
from UrlData import UrlData
from linkcheck import _

class HostCheckingUrlData(UrlData):
    "Url link for which we have to connect to a specific host"

    def __init__(self, urlName, recursionLevel, parentName = None,
                 baseRef = None, line=0, name=""):
        UrlData.__init__(self, urlName, recursionLevel,
	                 parentName=parentName, baseRef=baseRef, line=line,
			 name=name)
        self.host = None
        self.url = urlName

    def buildUrl(self):
        # to avoid anchor checking
        self.urlTuple=None
        
    def getCacheKey(self):
        return self.get_scheme()+":"+self.host

    def checkConnection(self, config):
        ip = socket.gethostbyname(self.host)
        self.setValid(self.host+"("+ip+") "+_("found"))
