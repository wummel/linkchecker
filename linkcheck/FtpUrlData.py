# -*- coding: iso-8859-1 -*-
"""Handle FTP links"""
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

import ftplib, i18n
from linkcheck import extensions, LinkCheckerError
from debug import *
from urllib import splitpasswd
from ProxyUrlData import ProxyUrlData
from HttpUrlData import HttpUrlData
from UrlData import ExcList

ExcList.extend([
   ftplib.error_reply,
   ftplib.error_temp,
   ftplib.error_perm,
   ftplib.error_proto,
])

class FtpUrlData (ProxyUrlData):
    """
    Url link with ftp scheme.
    """
    def checkConnection (self):
        # proxy support (we support only http)
        self.setProxy(self.config["proxy"].get(self.scheme))
        if self.proxy:
            http = HttpUrlData(self.urlName,
                  self.recursionLevel,
                  self.config,
                  parentName=self.parentName,
                  baseRef=self.baseRef,
                  line=self.line,
                  column=self.column,
		  name=self.name)
            http.buildUrl()
            return http.check()
        # using no proxy here
        # get login credentials
        if self.userinfo:
            _user, _password = splitpasswd(self.userinfo)
        else:
            _user, _password = self.getUserPassword()
        if _user is None or _password is None:
            raise LinkCheckerError(i18n._("No user or password found"))
        self.login(_user, _password)
        filename = self.cwd()
        if filename:
            self.retrieve(filename)
        return None


    def isHtml (self):
        if extensions['html'].search(self.url):
            return True
        return False


    def isParseable (self):
        for ro in extensions.values():
            if ro.search(self.url):
                return True
        return False


    def parseUrl (self):
        for key,ro in extensions.items():
            if ro.search(self.url):
                return getattr(self, "parse_"+key)()
        return None


    def login (self, _user, _password):
        """log into ftp server and check the welcome message"""
        # ready to connect
        try:
            self.urlConnection = ftplib.FTP()
            self.urlConnection.set_debuglevel(get_debuglevel())
            self.urlConnection.connect(self.urlparts[1])
            self.urlConnection.login(_user, _password)
        except EOFError:
            raise LinkCheckerError(i18n._("Remote host has closed connection"))
        if not self.urlConnection.getwelcome():
            self.closeConnection()
            raise LinkCheckerError(i18n._("Got no answer from FTP server"))
        # dont set info anymore, this may change every time we logged in
        #self.setInfo(info)


    def cwd (self):
        """change directory to given path"""
        # leeched from webcheck
        dirs = self.urlparts[2].split('/')
        filename = dirs.pop()
        if len(dirs) and not dirs[0]: del dirs[0]
        for d in dirs:
            self.urlConnection.cwd(d)
        return filename


    def retrieve (self, filename):
        """initiate download of given filename"""
        # it could be a directory if the trailing slash was forgotten
        try:
            self.urlConnection.cwd(filename)
            self.setWarning(i18n._("Missing trailing directory slash in ftp url"))
            return
        except ftplib.error_perm:
            pass
        self.urlConnection.voidcmd('TYPE I')
        conn, size = self.urlConnection.ntransfercmd('RETR %s'%filename)
        if size:
            self.dlsize = size
            # dont download data XXX recursion
            #page = conn.makefile().read(size)
        #else:
        #    page = conn.makefile().read()


    def closeConnection (self):
        try: self.urlConnection.closet()
        except: pass
        self.urlConnection = None
