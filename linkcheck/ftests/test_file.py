# -*- coding: iso-8859-1 -*-
"""test file parsing"""
# Copyright (C) 2004  Bastian Kleineidam
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
import os

import linkcheck.ftests


class TestFile (linkcheck.ftests.StandardTest):
    """test file:// link checking (and file content parsing)"""

    def test_html (self):
        """test links of file.html"""
        self.file_test("file.html")

    def test_text (self):
        """test links of file.txt"""
        self.file_test("file.txt")

    def test_asc (self):
        """test links of file.asc"""
        self.file_test("file.asc")

    def test_css (self):
        """test links of file.css"""
        self.file_test("file.css")

    def test_files (self):
        """test some direct file links"""
        attrs = {'curdir': os.getcwd(),
                 'datadir': 'linkcheck/ftests/data',
                }
        # good file
        url = "file://%(curdir)s/%(datadir)s/file.txt" % attrs
        resultlines = [
            "url %r" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "valid",
        ]
        self.direct(url, resultlines)
        # bad file
        url = "file:/%(curdir)s/%(datadir)s/file.txt" % attrs
        resultlines = [
            "url %r" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "error",
        ]
        self.direct(url, resultlines)
        # good file (missing double slash)
        url = "file:%(curdir)s/%(datadir)s/file.txt" % attrs
        nurl = linkcheck.url.url_norm(url)
        resultlines = [
            "url %r" % url,
            "cache key file://%(curdir)s/%(datadir)s/file.txt" % attrs,
            "real url file://%(curdir)s/%(datadir)s/file.txt" % attrs,
            "warning Base URL is not properly normed. Normed url is %r." % nurl,
            "valid",
        ]
        self.direct(url, resultlines)
        # good dir
        url = "file://%(curdir)s/%(datadir)s/" % attrs
        resultlines = [
            "url %r" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "valid",
        ]
        self.direct(url, resultlines)


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFile))
    return suite


if __name__ == '__main__':
    unittest.main()
