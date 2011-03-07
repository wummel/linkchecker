# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2010 Bastian Kleineidam
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
Test whitespace handling.
"""
from . import LinkCheckTest


class TestWhitespace (LinkCheckTest):
    """
    Test whitespace in URLs.
    """

    def test_leading_whitespace (self):
        # Leading whitespace
        url = u" http://www.heise.de/"
        attrs = self.get_attrs(url=url)
        attrs['nurl'] = self.norm(url.strip())
        resultlines = [
            u"url %(nurl)s" % attrs,
            u"cache key %(nurl)s" % attrs,
            u"real url %(nurl)s" % attrs,
            u"warning Leading or trailing whitespace in URL `%(url)s'." % attrs,
            u"valid",
        ]
        self.direct(url, resultlines)
        url = u"\nhttp://www.heise.de/"
        attrs = self.get_attrs(url=url)
        attrs['nurl'] = self.norm(url.strip())
        resultlines = [
            u"url %(nurl)s" % attrs,
            u"cache key %(nurl)s" % attrs,
            u"real url %(nurl)s" % attrs,
            u"warning Leading or trailing whitespace in URL `%(url)s'." % attrs,
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_trailing_whitespace (self):
        # Trailing whitespace
        url = u"http://www.heise.de/ "
        nurl = self.norm(url.strip())
        resultlines = [
            u"url %s" % nurl,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Leading or trailing whitespace in URL `%s'." % url,
            u"valid",
        ]
        self.direct(url, resultlines)
        url = u"http://www.heise.de/\n"
        nurl = self.norm(url.strip())
        resultlines = [
            u"url %s" % nurl,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Leading or trailing whitespace in URL `%s'." % url,
            u"valid",
        ]
        self.direct(url, resultlines)
