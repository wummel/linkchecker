# -*- coding: iso-8859-1 -*-
"""test ftp checking"""
# Copyright (C) 2004-2005  Bastian Kleineidam
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

import unittest

import linkcheck.ftests


class TestFtp (linkcheck.ftests.StandardTest):
    """test ftp: link checking"""

    needed_resources = ['network']

    def test_ftp (self):
        """test ftp link"""
        # ftp two slashes
        url = u"ftp://ftp.debian.org/"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_ftp_slashes (self):
        """test ftp links with missing slashes"""
        # ftp one slash
        url = u"ftp:/ftp.debian.org/"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed url is %s." % nurl,
            u"error",
        ]
        self.direct(url, resultlines)
        # missing path
        url = u"ftp://ftp.debian.org"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed url is %s." % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)
        # missing trailing dir slash
        url = u"ftp://ftp.debian.org/debian"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s/" % nurl,
            u"warning Missing trailing directory slash in ftp url.",
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_ftp_many_slashes (self):
        """test ftp links with too many slashes"""
        # ftp two dir slashes
        url = u"ftp://ftp.debian.org//debian/"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed url is %s." % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)
        # ftp many dir slashes
        url = u"ftp://ftp.debian.org////////debian/"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed url is %s." % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)
        # ftp three slashes
        url = u"ftp:///ftp.debian.org/"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"error",
        ]
        self.direct(url, resultlines)


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFtp))
    return suite


if __name__ == '__main__':
    unittest.main()
