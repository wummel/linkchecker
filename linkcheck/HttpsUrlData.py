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

import httplib
from UrlData import UrlData
from HttpUrlData import HttpUrlData
import linkcheck, Config
_supportHttps = hasattr(httplib, "HTTPS")


class HttpsUrlData(HttpUrlData):
    """Url link with https scheme"""

    def _getHTTPObject(self, host):
        h = httplib.HTTPS()
        h.set_debuglevel(Config.DebugLevel)
        h.connect(host)
        return h


    def _check(self, config):
        if _supportHttps:
            HttpUrlData._check(self, config)
        else:
            self.setWarning(linkcheck._("HTTPS url ignored"))
            self.logMe(config)
