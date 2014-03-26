# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2014 Bastian Kleineidam
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
Test news checking.
"""
from tests import need_network
from . import LinkCheckTest


class TestHttps (LinkCheckTest):
    """
    Test https: link checking.
    """

    @need_network
    def test_https (self):
        url = u"https://www.amazon.com/"
        rurl = u"http://www.amazon.com/"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % rurl,
            #u"info SSL cipher RC4-SHA, TLSv1/SSLv3.",
            u"info Redirected to `%s'." % rurl,
            u"valid",
        ]
        confargs = dict(
            #enabledplugins=['SslCertificateCheck'],
            #SslCertificateCheck=dict(sslcertwarndays=10),
        )
        self.direct(url, resultlines, recursionlevel=0, confargs=confargs)
