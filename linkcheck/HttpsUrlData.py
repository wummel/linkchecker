"""Handle https links"""
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

from UrlData import UrlData
from HttpUrlData import HttpUrlData
import linkcheck, Config
import linkcheck.httplib as httplib
_supportHttps = hasattr(httplib, "HTTPSConnection")


class HttpsUrlData (HttpUrlData):
    """Url link with https scheme"""

    def _getHTTPObject (self, host):
        h = httplib.HTTPSConnection(host)
        h.set_debuglevel(Config.DebugLevel)
        h.connect()
        return h

    def _check (self):
        if _supportHttps:
            HttpUrlData._check(self)
        else:
            self.setWarning(linkcheck._("%s url ignored")%self.scheme.capitalize())
            self.logMe()
