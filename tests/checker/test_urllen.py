# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012-2014 Bastian Kleineidam
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
Test URL length checks.
"""
from . import LinkCheckTest
from linkcheck.checker.const import URL_MAX_LENGTH


class TestURLLength(LinkCheckTest):
    """
    Test URL lengths.
    """

    def test_url_warn(self):
        url = u"http://www.example.org/" + (u"a" * URL_MAX_LENGTH)
        attrs = self.get_attrs(url=url)
        attrs['nurl'] = self.norm(url)
        resultlines = [
            u"url %(nurl)s" % attrs,
            u"cache key %(nurl)s" % attrs,
            u"real url %(nurl)s" % attrs,
            u"warning URL length %d is longer than %d." % (len(url), URL_MAX_LENGTH),
            u"error",
        ]
        self.direct(url, resultlines)
