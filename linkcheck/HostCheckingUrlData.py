# -*- coding: iso-8859-1 -*-
"""Base handle for links with a hostname"""
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

import socket, urllib
from UrlData import UrlData
from linkcheck import i18n

class HostCheckingUrlData (UrlData):
    "Url link for which we have to connect to a specific host"

    def __init__ (self, urlName, recursionLevel, config, parentName=None,
                  baseRef=None, line=0, column=0, name=""):
        super(HostCheckingUrlData, self).__init__(urlName, recursionLevel,
                    config, parentName=parentName, baseRef=baseRef,
                    line=line, column=column, name=name)
        self.host = None
        self.url = urllib.unquote(self.urlName)


    def buildUrl (self):
        # to avoid anchor checking
        self.urlparts = None


    def getCacheKeys (self):
        return ["%s:%s" % (self.scheme, self.host)]


    def checkConnection (self):
        ip = socket.gethostbyname(self.host)
        self.setValid(self.host+"("+ip+") "+i18n._("found"))
