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
Test html anchor parsing and checking.
"""
from . import LinkCheckTest


class TestAnchor (LinkCheckTest):
    """
    Test anchor checking of HTML pages.
    """

    def test_anchor (self):
        confargs = {"enabledplugins": ["AnchorCheck"]}
        url = u"file://%(curdir)s/%(datadir)s/anchor.html" % self.get_attrs()
        nurl = self.norm(url)
        anchor = "broken"
        urlanchor = url + "#" + anchor
        resultlines = [
            u"url %s" % urlanchor,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Anchor `%s' not found. Available anchors: `myid:'." % anchor,
            u"valid",
        ]
        self.direct(urlanchor, resultlines, confargs=confargs)

