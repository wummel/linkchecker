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
import time
import urllib
import cStringIO as StringIO

import linkcheck
import urlbase
import proxysupport
import httpurl


class FtpUrl (urlbase.UrlBase, proxysupport.ProxySupport):
    """Url link with ftp scheme."""

    def __init__ (self, base_url, recursion_level, consumer,
                  parent_url = None,
                  base_ref = None, line=0, column=0, name=""):
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
        # using no proxy here
        # get login credentials
        if self.userinfo:
            _user, _password = urllib.splitpasswd(self.userinfo)
        else:
            _user, _password = self.get_user_password()
        self.login(_user, _password)
        self.filename = self.cwd()
        self.listfile(self.filename)
        if self.is_directory():
            self.url_connection.cwd(self.filename)
            self.files = self.get_files()
        else:
            self.files = []
        return None

    def login (self, _user, _password):
        """log into ftp server and check the welcome message"""
        # ready to connect
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
        except EOFError:
            raise linkcheck.LinkCheckerError(
                                       _("Remote host has closed connection"))
        if not self.url_connection.getwelcome():
            self.close_connection()
            raise linkcheck.LinkCheckerError(
                                       _("Got no answer from FTP server"))
        # don't set info anymore, this may change every time we log in
        #self.add_info(info)

    def cwd (self):
        """Change to URL parent directory. Return filename of last path
           component.
        """
        dirname = self.urlparts[2].strip('/')
        dirs = dirname.split('/')
        filename = dirs.pop()
        self.url_connection.cwd('/')
        for d in dirs:
            self.url_connection.cwd(d)
        return filename

    def listfile (self, filename):
        """see if filename is in the current FTP directory"""
        files = self.url_connection.nlst()
        linkcheck.log.debug(linkcheck.LOG_CHECK, "FTP files %s", str(files))
        if filename and filename not in files:
            raise ftplib.error_perm, "550 File not found"

    def get_files (self):
        """Get list of filenames in directory. Subdirectories have an
           ending slash.
        """
        # Rudimentary LIST output parsing. An entry is assumed to have
        # the following form:
        # drwxr-xr-x   8 root     wheel        1024 Jan  3  1994 foo
        # Symbolic links are assumed to have the following form:
        # drwxr-xr-x   8 root     wheel        1024 Jan  3  1994 foo -> bar
        files = []
        def add_entry (line):
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Directory entry %r",
                                line)
            parts = line.split()
            if len(parts) >= 8:
                if parts[-2] == "->":
                    # symbolic link
                    fname = parts[-3]
                else:
                    fname = parts[-1]
                if fname not in (".", ".."):
                    if line.startswith("d"):
                        # a directory
                        fname += "/"
                    files.append(fname)
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
        # it could be a directory if the trailing slash was forgotten
        if self.filename is not None and not self.url.endswith('/'):
            try:
                self.url_connection.cwd(self.filename)
                self.add_warning(_("Missing trailing directory slash in ftp url"))
                self.url += '/'
                self.cwd()
            except ftplib.error_perm, msg:
                pass
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
            self.data = linkcheck.checker.get_index_html(self.files)
        else:
            # download file in BINARY mode
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
        self.url_connection.close()
        self.url_connection = None
