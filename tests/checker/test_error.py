# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2008 Bastian Kleineidam
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
Test error checking.
"""

import unittest
from . import LinkCheckTest


class TestError (LinkCheckTest):
    """
    Test unrecognized or syntactically wrong links.
    """

    def test_unrecognized (self):
        """
        Unrecognized scheme test.
        """
        url = u"hutzli:"
        attrs = self.get_attrs(url=url)
        attrs['nurl'] = self.norm("file://%(curdir)s/%(url)s" % attrs)
        resultlines = [
            u"url %(nurl)s" % attrs,
            u"cache key %(nurl)s" % attrs,
            u"real url %(nurl)s" % attrs,
            u"error",
        ]
        self.direct(url, resultlines)

    def test_leading_whitespace (self):
        """
        Leading whitespace test.
        """
        url = u" http://www.heise.de/"
        attrs = self.get_attrs(url=url)
        attrs['nurl'] = self.norm("file://%(curdir)s/%(url)s" % attrs)
        resultlines = [
            u"url %(nurl)s" % attrs,
            u"cache key %(nurl)s" % attrs,
            u"real url %(nurl)s" % attrs,
            u"error",
        ]
        self.direct(url, resultlines)
        url = u"\nhttp://www.heise.de/"
        attrs = self.get_attrs(url=url)
        attrs['nurl'] = self.norm("file://%(curdir)s/%(url)s" % attrs)
        resultlines = [
            u"url %(nurl)s" % attrs,
            u"cache key %(nurl)s" % attrs,
            u"real url %(nurl)s" % attrs,
            u"error",
        ]
        self.direct(url, resultlines)

    def test_trailing_whitespace (self):
        """
        Trailing whitespace test.
        """
        url = u"http://www.heise.de/ "
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed URL is %s." % nurl,
            u"error",
        ]
        self.direct(url, resultlines)
        url = u"http://www.heise.de/\n"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed URL is %s." % nurl,
            u"error",
        ]
        self.direct(url, resultlines)

    def test_invalid1 (self):
        # invalid scheme chars
        url = u"äöü?:"
        attrs = self.get_attrs(url=url)
        attrs['nurl'] = self.norm("file://%(curdir)s/%(url)s" % attrs)
        resultlines = [
            u"url %(nurl)s" % attrs,
            u"cache key %(nurl)s" % attrs,
            u"real url %(nurl)s" % attrs,
            u"error",
        ]
        self.direct(url, resultlines)

    def test_invalid2 (self):
        # missing scheme alltogether
        url = u"?äöü?"
        attrs = self.get_attrs(url=url)
        attrs['nurl'] = self.norm("file://%(curdir)s/%(url)s" % attrs)
        resultlines = [
            u"url %(nurl)s" % attrs,
            u"cache key %(nurl)s" % attrs,
            u"real url %(nurl)s" % attrs,
            u"error",
        ]
        self.direct(url, resultlines)

    def test_invalid3 (self):
        # really fucked up
        url = u"@³²¼][½ ³@] ¬½"
        attrs = self.get_attrs(url=url)
        attrs['nurl'] = self.norm("file://%(curdir)s/%(url)s" % attrs)
        resultlines = [
            u"url %(nurl)s" % attrs,
            u"cache key %(nurl)s" % attrs,
            u"real url %(nurl)s" % attrs,
            u"error",
        ]
        self.direct(url, resultlines)


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestError)


if __name__ == '__main__':
    unittest.main()
