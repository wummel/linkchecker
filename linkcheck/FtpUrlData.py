"""Handle FTP links"""
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

import ftplib, linkcheck
from UrlData import UrlData,ExcList

ExcList.extend([
   ftplib.error_reply,
   ftplib.error_temp,
   ftplib.error_perm,
   ftplib.error_proto,
])

class FtpUrlData (UrlData):
    """
    Url link with ftp scheme.
    """

    def checkConnection (self):
        _user, _password = self._getUserPassword()
        if _user is None or _password is None:
            raise linkcheck.error, linkcheck._("No user or password found")
        try:
            self.urlConnection = ftplib.FTP(self.urlTuple[1], _user, _password)
        except EOFError:
            raise linkcheck.error, linkcheck._("Remote host has closed connection")
        info = self.urlConnection.getwelcome()
        if not info:
            self.closeConnection()
            raise linkcheck.error, linkcheck._("Got no answer from FTP server")
        self.setInfo(info)


    def closeConnection (self):
        try: self.urlConnection.quit()
        except: pass
        self.urlConnection = None
