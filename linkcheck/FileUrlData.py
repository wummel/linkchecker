"""Handle local file: links"""
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

import re, os, urlparse, urllib
from UrlData import UrlData, ExcList
from linkcheck import _

# OSError is thrown on Windows when a file is not found
ExcList.append(OSError)

html_re = re.compile(r'(?i)\.s?html?$')
html_content_re = re.compile(r'(?i)<html>.*</html>')
opera_re = re.compile(r'^(?i)opera.adr$')
opera_content_re = re.compile(r'(?i)Opera Hotlist')

class FileUrlData(UrlData):
    "Url link with file scheme"

    def __init__(self,
                 urlName, 
                 recursionLevel, 
                 parentName = None,
                 baseRef = None, line=0, name=""):
        UrlData.__init__(self,
                 urlName, 
                 recursionLevel,
                 parentName=parentName,
                 baseRef=baseRef, line=line, name=name)
        if not parentName and not baseRef and \
           not re.compile("^file:").search(self.urlName):
            self.urlName = os.path.expanduser(self.urlName)
            winre = re.compile("^[a-zA-Z]:")
            if winre.search(self.urlName):
                self.adjustWinPath()
            else:
                if self.urlName[0:1] != "/":
                    self.urlName = os.getcwd()+"/"+self.urlName
                    if winre.search(self.urlName):
                        self.adjustWinPath()
            self.urlName = self.urlName.replace("\\", "/")
            self.urlName = "file://"+self.urlName


    def buildUrl(self):
        UrlData.buildUrl(self)
        # cut off parameter, query and fragment
        self.url = urlparse.urlunparse(self.urlTuple[:3] + ('','',''))


    def adjustWinPath(self):
        "c:\\windows ==> /c|\\windows"
        self.urlName = "/"+self.urlName[0]+"|"+self.urlName[2:]


    def isHtml(self):
        if html_re.search(self.url) or opera_re.search(self.url):
            return 1
        # try to read content (can fail, so catch error)
        try:
            return html_content_re.search(self.getContent()) or \
                   opera_content_re.search(self.getContent())
        except IOError:
            pass
        return None


    def parseUrl(self, config):
        if html_re.search(self.url) or \
           html_content_re.search(self.getContent()):
            UrlData.parseUrl(self, config)
            return
        # parse an opera bookmark file
        name = ""
        lineno = 0
        for line in self.getContent().split("\n"):
            lineno += 1
            line = line.strip()
            if line.startswith("NAME="):
                name = line[5:]
            elif line.startswith("URL="):
                url = line[4:]
                if url:
                    from UrlData import GetUrlDataFrom
                    config.appendUrl(GetUrlDataFrom(url,
                        self.recursionLevel+1, self.url, None, lineno, name))
                name = ""
