# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2012 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
FTP checking.
"""
from .. import need_pyftpdlib
from .ftpserver import FtpServerTest


class TestFtp (FtpServerTest):
    """Test ftp: link checking."""

    @need_pyftpdlib
    def test_ftp (self):
        # ftp two slashes
        url = u"ftp://%s:%d/" % (self.host, self.port)
        resultlines = [
          u"url %s" % url,
          u"cache key %s" % url,
          u"real url %s" % url,
          u"valid",
        ]
        # ftp use/password
        user = "anonymous"
        passwd = "Ftp"
        url = u"ftp://%s:%s@%s:%d/" % (user, passwd, self.host, self.port)
        resultlines = [
          u"url %s" % url,
          u"cache key %s" % url,
          u"real url %s" % url,
          u"valid",
        ]
        self.direct(url, resultlines)
        # ftp one slash
        url = u"ftp:/%s:%d/" % (self.host, self.port)
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key None",
            u"real url %s" % nurl,
            u"error",
        ]
        self.direct(url, resultlines)
        # missing path
        url = u"ftp://%s:%d" % (self.host, self.port)
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)
        # missing trailing dir slash
        url = u"ftp://%s:%d/base" % (self.host, self.port)
        nurl = self.norm(url)
        resultlines = [
        u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s/" % nurl,
            u"warning Missing trailing directory slash in ftp url.",
            u"valid",
        ]
        self.direct(url, resultlines)
        # ftp two dir slashes
        url = u"ftp://%s:%d//base/" % (self.host, self.port)
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)
        # ftp many dir slashes
        url = u"ftp://%s:%d////////base/" % (self.host, self.port)
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)
        # ftp three slashes
        url = u"ftp:///%s:%d/" % (self.host, self.port)
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key None",
            u"real url %s" % nurl,
            u"error",
        ]
        self.direct(url, resultlines)
