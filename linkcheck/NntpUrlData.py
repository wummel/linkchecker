# -*- coding: iso-8859-1 -*-
"""Handle nntp: and news: links"""
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

import re, time, sys, nntplib, urlparse, random, i18n
from linkcheck import LinkCheckerError, Config
from UrlData import ExcList, UrlData
from debug import *
random.seed()

ExcList.extend([nntplib.error_reply,
               nntplib.error_temp,
               nntplib.error_perm,
               nntplib.error_proto,
               EOFError,
               ])

class NntpUrlData (UrlData):
    "Url link with NNTP scheme"

    def buildUrl (self):
        # use nntp instead of news to comply with the unofficial internet
	# draft of Alfred Gilman which unifies (s)news and nntp URLs
        # note: we use this only internally (for parsing and caching)
        if self.urlName[:4].lower()=='news':
            self.url = 'nntp'+self.urlName[4:]
        else:
            self.url = self.urlName
        self.urlparts = urlparse.urlsplit(self.url)
        Config.debug(BRING_IT_ON, self.urlparts)


    def checkConnection (self):
        nntpserver = self.urlparts[1] or self.config["nntpserver"]
        if not nntpserver:
            self.setWarning(i18n._("No NNTP server specified, skipping this URL"))
            return
        nntp = self._connectNntp(nntpserver)
        group = self.urlparts[2]
        while group[:1]=='/':
            group = group[1:]
        if '@' in group:
            # request article
            resp,number,id = nntp.stat("<"+group+">")
            self.setInfo(i18n._('Articel number %s found') % number)
        else:
            # split off trailing articel span
            group = group.split('/',1)[0]
            if group:
                # request group info
                resp,count,first,last,name = nntp.group(group)
                self.setInfo(i18n._("Group %s has %s articles, range %s to %s") %\
                             (name, count, first, last))
            else:
                # group name is the empty string
                self.setWarning(i18n._("No newsgroup specified in NNTP URL"))


    def _connectNntp (self, nntpserver):
        """This is done only once per checking task. Also, the newly
        introduced error codes 504 and 505 (both inclining "Too busy, retry
        later", are caught."""
        tries = 0
        nntp = value = None
        while tries < 5:
            tries += 1
            try:
                nntp=nntplib.NNTP(nntpserver)
            except nntplib.error_perm:
                value = sys.exc_info()[1]
                if re.compile("^50[45]").search(str(value)):
                    time.sleep(random.randrange(10,30))
                else:
                    raise
        if nntp is None:
            raise LinkCheckerError(i18n._("NTTP server too busy; tried more than %d times")%tries)
        if value is not None:
            self.setWarning(i18n._("NNTP busy: %s")%str(value))
        return nntp


    def getCacheKeys (self):
        return [self.url]


    def hasContent (self):
        return False
