""" linkcheck/NntpUrlData.py

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
import re,string,time,sys,nntplib,urlparse,linkcheck
from linkcheck import _
from UrlData import ExcList,UrlData
debug = linkcheck.Config.debug

ExcList.extend([nntplib.error_reply,
               nntplib.error_temp,
               nntplib.error_perm,
               nntplib.error_proto,
               ])

class NntpUrlData(UrlData):
    "Url link with NNTP scheme"
    
    def get_scheme(self):
        return "nntp"

    def buildUrl(self):
        # use nntp instead of news to comply with the unofficial internet
	# draft of Alfred Gilman which unifies (s)news and nntp URLs
        # note: we use this only internally (for parsing and caching)
        if string.lower(self.urlName[:4])=='news':
            self.url = 'nntp'+self.urlName[4:]
        else:
            self.url = self.urlName
        self.urlTuple = urlparse.urlparse(self.url)
        debug("DEBUG: %s\n" % `self.urlTuple`)


    def checkConnection(self, config):
        nntpserver = self.urlTuple[1] or config["nntpserver"]
        if not nntpserver:
            self.setWarning(_("No NNTP server specified, skipping this URL"))
            return
        nntp = self._connectNntp(nntpserver)
        group = self.urlTuple[2]
        while group[:1]=='/':
            group = group[1:]
        if '@' in group:
            # request article
            resp,number,id = nntp.stat("<"+group+">")
            self.setInfo(_('Articel number %s found' % number))
        else:
            # split off trailing articel span
            group = string.split(group,'/',1)[0]
            if group:
                # request group info
                resp,count,first,last,name = nntp.group(group)
                self.setInfo(_("Group %s has %s articles, range %s to %s") %\
                             (name, count, first, last))
            else:
                # group name is the empty string
                self.setWarning(_("No newsgroup specified in NNTP URL"))


    def _connectNntp(self, nntpserver):
        """This is done only once per checking task."""
        timeout = 1
        while timeout:
            try:
                nntp=nntplib.NNTP(nntpserver)
                timeout = 0
            except nntplib.error_perm:
                value = sys.exc_info()[1]
                debug("NNTP: %s\n" % value)
                if re.compile("^505").search(str(value)):
                    import whrandom
                    time.sleep(whrandom.randint(10,20))
                else:
                    raise
        return nntp


    def getCacheKey(self):
        return self.url
