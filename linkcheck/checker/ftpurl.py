# -*- coding: iso-8859-1 -*-
"""Handle FTP links"""
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

import ftplib
import urllib

import linkcheck
import urlbase
import proxysupport
import httpurl

from linkcheck.i18n import _


class FtpUrl (urlbase.UrlBase, proxysupport.ProxySupport):
    """Url link with ftp scheme."""

    def check_connection (self):
        # proxy support (we support only http)
        self.set_proxy(self.config["proxy"].get(self.scheme))
        if self.proxy:
            http = httpurl.HttpUrl(self.base_url,
                  self.recursion_level,
                  self.config,
                  parent_url=self.parent_url,
                  base_ref=self.base_ref,
                  line=self.line,
                  column=self.column,
                  name=self.name)
            http.build_url()
            return http.check()
        # using no proxy here
        # get login credentials
        if self.userinfo:
            _user, _password = urllib.splitpasswd(self.userinfo)
        else:
            _user, _password = self.get_user_password()
        if _user is None or _password is None:
            raise linkcheck.LinkCheckerError(_("No user or password found"))
        self.login(_user, _password)
        filename = self.cwd()
        if filename:
            self.retrieve(filename)
        return None

    def is_html (self):
        if linkcheck.checker.extensions['html'].search(self.url):
            return True
        return False

    def is_parseable (self):
        for ro in linkcheck.checker.extensions.values():
            if ro.search(self.url):
                return True
        return False

    def parse_url (self):
        for key, ro in linkcheck.checker.extensions.items():
            if ro.search(self.url):
                return getattr(self, "parse_"+key)()
        return None

    def login (self, _user, _password):
        """log into ftp server and check the welcome message"""
        # ready to connect
        try:
            self.url_connection = ftplib.FTP()
            if self.config.get("debug"):
                self.url_connection.set_debuglevel(1)
            self.url_connection.connect(self.urlparts[1])
            self.url_connection.login(_user, _password)
        except EOFError:
            raise linkcheck.LinkCheckerError(
                                       _("Remote host has closed connection"))
        if not self.url_connection.getwelcome():
            self.close_connection()
            raise linkcheck.LinkCheckerError(
                                       _("Got no answer from FTP server"))
        # dont set info anymore, this may change every time we logged in
        #self.add_info(info)

    def cwd (self):
        """change directory to given path"""
        # leeched from webcheck
        dirs = self.urlparts[2].split('/')
        filename = dirs.pop()
        if len(dirs) and not dirs[0]: del dirs[0]
        for d in dirs:
            self.url_connection.cwd(d)
        return filename

    def retrieve (self, filename):
        """initiate download of given filename"""
        # it could be a directory if the trailing slash was forgotten
        try:
            self.url_connection.cwd(filename)
            self.add_warning(_("Missing trailing directory slash in ftp url"))
            return
        except ftplib.error_perm:
            pass
        self.url_connection.voidcmd('TYPE I')
        conn, size = self.url_connection.ntransfercmd('RETR %s'%filename)
        if size:
            self.dlsize = size
            # dont download data XXX recursion
            #page = conn.makefile().read(size)
        #else:
        #    page = conn.makefile().read()

    def close_connection (self):
        try: self.url_connection.closet()
        except: pass
        self.url_connection = None
