# -*- coding: iso-8859-1 -*-
"""Handle local file: links"""
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

import re
import os
import urlparse
import UrlData

# if file extension was fruitless, look at the content
contents = {
    "html": re.compile(r'(?i)<html>.*</html>'),
    "opera" : re.compile(r'Opera Hotlist'),
#    "text" : re.compile(r'[\w\s]+'),
}

_schemes = r"""(
acap        # application configuration access protocol
|afs        # Andrew File System global file names
|cid        # content identifier
|data       # data
|dav        # dav
|fax        # fax
|imap       # internet message access protocol
|ldap       # Lightweight Directory Access Protocol
|mailserver # Access to data available from mail servers
|mid        # message identifier
|modem      # modem
|nfs        # network file system protocol
|opaquelocktoken # opaquelocktoken
|pop        # Post Office Protocol v3
|prospero   # Prospero Directory Service
|rtsp       # real time streaming protocol
|service    # service location
|sip        # session initiation protocol
|tel        # telephone
|tip        # Transaction Internet Protocol
|tn3270     # Interactive 3270 emulation sessions
|vemmi      # versatile multimedia interface
|wais       # Wide Area Information Servers
|z39\.50r   # Z39.50 Retrieval
|z39\.50s   # Z39.50 Session
|chrome     # Mozilla specific
|find       # Mozilla specific
|clsid      # Microsoft specific
|javascript # JavaScript
|isbn       # ISBN (int. book numbers)
|https?     # HTTP/HTTPS
|ftp        # FTP
|file       # local file
|telnet     # telnet
|mailto     # mailto
|gopher     # gopher
|s?news     # news
|nntp       # news
)"""

class FileUrlData (UrlData.UrlData):
    "Url link with file scheme"

    def __init__ (self,
                  urlName,
                  config,
                  recursionLevel,
                  parentName = None,
                  baseRef = None, line=0, column=0, name=""):
        super(FileUrlData, self).__init__(urlName, config, recursionLevel,
                                    parentName=parentName, baseRef=baseRef,
                                    line=line, column=column, name=name)
        if not (parentName or baseRef or self.urlName.startswith("file:")):
            self.urlName = os.path.expanduser(self.urlName)
            if not self.urlName.startswith("/"):
                self.urlName = os.getcwd()+"/"+self.urlName
            self.urlName = "file://"+self.urlName
        self.urlName = self.urlName.replace("\\", "/")
        # transform c:/windows into /c|/windows
        self.urlName = re.sub(r"^file://(/?)([a-zA-Z]):", r"file:///\2|",
                              self.urlName)

    def buildUrl (self):
        super(FileUrlData, self).buildUrl()
        # ignore query and fragment url parts for filesystem urls
        self.urlparts[3] = self.urlparts[4] = ''
        self.url = urlparse.urlunsplit(self.urlparts)

    def getCacheKeys (self):
        # the host in urlparts is lowercase()d
        if self.urlparts:
            self.urlparts[4] = self.anchor
            key = urlparse.urlunsplit(self.urlparts)
            self.urlparts[4] = ''
            return [key]
        return []

    def isHtml (self):
        if linkcheck.extensions['html'].search(self.url):
            return True
        if contents['html'].search(self.getContent()[:20]):
            return True
        return False

    def isFile (self):
        return True

    def isParseable (self):
        # guess by extension
        for ro in linkcheck.extensions.values():
            if ro.search(self.url):
                return True
        # try to read content (can fail, so catch error)
        try:
            for ro in contents.values():
                if ro.search(self.getContent()[:20]):
                    return True
        except IOError:
            pass
        return False

    def parseUrl (self):
        for key, ro in linkcheck.extensions.items():
            if ro.search(self.url):
                return getattr(self, "parse_"+key)()
        for key, ro in contents.items():
            if ro.search(self.getContent()[:20]):
                return getattr(self, "parse_"+key)()
        return None
