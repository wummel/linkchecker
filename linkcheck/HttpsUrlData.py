# -*- coding: iso-8859-1 -*-
"""Handle https links"""
# Copyright (C) 2000-2003  Bastian Kleineidam
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

import Config, httplib, i18n
from UrlData import UrlData
from HttpUrlData import HttpUrlData
from linkcheck.debug import *
_supportHttps = hasattr(httplib, "HTTPSConnection")


class HttpsUrlData (HttpUrlData):
    """Url link with https scheme"""

    def _getHTTPObject (self, host):
        h = httplib.HTTPSConnection(host)
        h.set_debuglevel(get_debuglevel())
        h.connect()
        return h

    def _check (self):
        if _supportHttps:
            HttpUrlData._check(self)
        else:
            self.setWarning(i18n._("%s url ignored")%self.scheme.capitalize())
            self.logMe()
