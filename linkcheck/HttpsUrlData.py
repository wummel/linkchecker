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
from linkcheck import _
_supportHttps=1
try:
    from linkcheckssl import httpslib
except ImportError:
    _supportHttps=0


class HttpsUrlData(HttpUrlData):
    """Url link with https scheme"""

    def _getHTTPObject(self, host):
        h = httpslib.HTTPS()
        h.connect(host)
        return h

    def check(self, config):
        if _supportHttps:
            HttpUrlData.check(self, config)
        else:
            self.setWarning(_("HTTPS url ignored"))
            self.logMe(config)

    def get_scheme(self):
        return "https"
