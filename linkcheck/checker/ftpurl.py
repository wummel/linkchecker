# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2005  Bastian Kleineidam
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
"""
Handle FTP links.
"""

import ftplib
import time
import urllib
import cStringIO as StringIO

import linkcheck
import urlbase
import proxysupport
import httpurl
import linkcheck.ftpparse._ftpparse as ftpparse

DEFAULT_TIMEOUT_SECS = 300


class FtpUrl (urlbase.UrlBase, proxysupport.ProxySupport):
    """
    Url link with ftp scheme.
    """

    def __init__ (self, base_url, recursion_level, consumer,
                  parent_url = None,
                  base_ref = None, line=0, column=0, name=u""):
        super(FtpUrl, self).__init__(base_url, recursion_level, consumer,
             parent_url=parent_url, base_ref=base_ref,
             line=line, column=column, name=name)
        # list of files for recursion
        self.files = []
        # last part of URL filename
        self.filename = None

    def check_connection (self):
        # proxy support (we support only http)
        self.set_proxy(self.consumer.config["proxy"].get(self.scheme))
        if self.proxy:
            # using a (HTTP) proxy
            http = httpurl.HttpUrl(self.base_url,
                  self.recursion_level,
                  self.consumer.config,
                  parent_url=self.parent_url,
                  base_ref=self.base_ref,
                  line=self.line,
                  column=self.column,
                  name=self.name)
            http.build_url()
            return http.check()
        self.login()
        self.filename = self.cwd()
        self.listfile()
        self.files = []
        return None

    def get_user_password (self):
        # get login credentials
        if self.userinfo:
            return urllib.splitpasswd(self.userinfo)
        return super(FtpUrl, self).get_user_password()

    def login (self):
        """
        Log into ftp server and check the welcome message.
        """
        # ready to connect
        _user, _password = self.get_user_password()
        key = ("ftp", self.urlparts[1], _user, _password)
        conn = self.consumer.cache.get_connection(key)
        if conn is not None and conn.sock is not None:
            # reuse cached FTP connection
            self.url_connection = conn
            return
        try:
            self.url_connection = ftplib.FTP()
            if self.consumer.config.get("debug"):
                self.url_connection.set_debuglevel(1)
            self.url_connection.connect(self.urlparts[1])
            if _user is None:
                self.url_connection.login()
            elif _password is None:
                self.url_connection.login(_user)
            else:
                self.url_connection.login(_user, _password)
        except EOFError, msg:
            msg = str(msg)
            raise linkcheck.LinkCheckerError(
                           _("Remote host has closed connection: %r") % msg)
        if not self.url_connection.getwelcome():
            self.close_connection()
            raise linkcheck.LinkCheckerError(
                                       _("Got no answer from FTP server"))
        # don't set info anymore, this may change every time we log in
        #self.add_info(info)

    def cwd (self):
        """
        Change to URL parent directory. Return filename of last path
        component.
        """
        dirname = self.urlparts[2].strip('/')
        dirs = dirname.split('/')
        filename = dirs.pop()
        self.url_connection.cwd('/')
        for d in dirs:
            self.url_connection.cwd(d)
        return filename

    def listfile (self):
        """
        See if filename is in the current FTP directory.
        """
        if not self.filename:
            return
        files = self.get_files()
        linkcheck.log.debug(linkcheck.LOG_CHECK, "FTP files %s", str(files))
        if self.filename in files:
            # file found
            return
        # it could be a directory if the trailing slash was forgotten
        if "%s/" % self.filename in files:
            if not self.url.endswith('/'):
                self.add_warning(
                         _("Missing trailing directory slash in ftp url."))
                self.url += '/'
            return
        raise ftplib.error_perm, "550 File not found"

    def get_files (self):
        """
        Get list of filenames in directory. Subdirectories have an
        ending slash.
        """
        files = []
        def add_entry (line):
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Directory entry %r",
                                line)
            try:
                fpo = ftpparse.parse(line)
                name = fpo.name
                if fpo.trycwd:
                    name += "/"
                if fpo.trycwd or fpo.tryretr:
                    files.append(name)
            except (ValueError, AttributeError), msg:
                linkcheck.log.debug(linkcheck.LOG_CHECK, "%s (%s)",
                                    str(msg), line)
        self.url_connection.dir(add_entry)
        return files

    def is_html (self):
        if linkcheck.checker.extensions['html'].search(self.url):
            return True
        return False

    def is_parseable (self):
        if self.is_directory():
            return True
        for ro in linkcheck.checker.extensions.values():
            if ro.search(self.url):
                return True
        return False

    def is_directory (self):
        return self.url.endswith('/')

    def parse_url (self):
        if self.is_directory():
            return self.parse_html()
        for key, ro in linkcheck.checker.extensions.items():
            if ro.search(self.url):
                return getattr(self, "parse_"+key)()
        return None

    def get_content (self):
        if not self.valid:
            return ""
        if self.has_content:
            return self.data
        t = time.time()
        if self.is_directory():
            self.url_connection.cwd(self.filename)
            self.files = self.get_files()
            self.data = linkcheck.checker.get_index_html(self.files)
        else:
            # download file in BINARY mode
            ftpcmd = "RETR %s" % self.filename
            buf = StringIO.StringIO()
            def stor_data (s):
                buf.write(s)
            self.url_connection.retrbinary(ftpcmd, stor_data)
            self.data = buf.getvalue()
            buf.close()
        self.dltime = time.time() - t
        self.dlsize = len(self.data)
        self.has_content = True
        return self.data

    def close_connection (self):
        if self.url_connection is None:
            return
        # add to cached connections
        _user, _password = self.get_user_password()
        key = ("ftp", self.urlparts[1], _user, _password)
        cache_add = self.consumer.cache.add_connection
        cache_add(key, self.url_connection, DEFAULT_TIMEOUT_SECS)
        self.url_connection = None
