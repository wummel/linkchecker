"""
    Copyright (C) 2000  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
import re,string,time,nntplib,linkcheck
from HostCheckingUrlData import HostCheckingUrlData
from linkcheck import _

nntp_re =  re.compile("^news:[\w.\-]+$")

class NntpUrlData(HostCheckingUrlData):
    "Url link with NNTP scheme"
    
    def buildUrl(self):
        HostCheckingUrlData.buildUrl(self)
        if not nntp_re.match(self.urlName):
            raise linkcheck.error, _("Illegal NNTP link syntax")
        self.host = string.lower(self.urlName[5:])


    def checkConnection(self, config):
        if not config["nntpserver"]:
            self.setWarning(_("No NNTP server specified, checked only syntax"))
        config.connectNntp()
        nntp = config["nntp"]
        resp,count,first,last,name = nntp.group(self.host)
        self.setInfo(_("Group %s has %s articles, range %s to %s") % \
                     (name, count, first, last))


    def getCacheKey(self):
        return "news:"+HostCheckingUrlData.getCacheKey(self)


    def __str__(self):
        return "NNTP link\n"+HostCheckingUrlData.__str__(self)

