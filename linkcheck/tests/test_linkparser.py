# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005  Bastian Kleineidam
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
Test linkparser routines.
"""

import unittest
import linkcheck.linkparse
import linkcheck.HtmlParser.htmlsax

class TestLinkparser (unittest.TestCase):
    """
    Test link parsing.
    """

    def _test_one_link (self, content, url):
        h = linkcheck.linkparse.LinkFinder(content)
        p = linkcheck.HtmlParser.htmlsax.parser(h)
        h.parser = p
        p.feed(content)
        p.flush()
        h.parser = None
        p.handler = None
        self.assert_(len(h.urls) == 1)
        purl = h.urls[0][0]
        self.assertEqual(purl, url)

    def test_href_parsing (self):
        """
        Test <a href> parsing.
        """
        content = '<a href="%s">'
        url = "alink"
        self._test_one_link(content % url, url)
        url = " alink"
        self._test_one_link(content % url, url)
        url = "alink "
        self._test_one_link(content % url, url)
        url = " alink "
        self._test_one_link(content % url, url)

    def test_css_parsing (self):
        """
        Test css style attribute parsing.
        """
        content = '<table style="background: url(%s) no-repeat" >'
        url = "alink"
        self._test_one_link(content % url, url)
        content = '<table style="background: url( %s) no-repeat" >'
        self._test_one_link(content % url, url)
        content = '<table style="background: url(%s ) no-repeat" >'
        self._test_one_link(content % url, url)
        content = '<table style="background: url( %s ) no-repeat" >'
        self._test_one_link(content % url, url)
        content = '<table style="background: url(\'%s\') no-repeat" >'
        self._test_one_link(content % url, url)
        content = "<table style='background: url(\"%s\") no-repeat' >"
        self._test_one_link(content % url, url)
        content = '<table style="background: url(\'%s\' ) no-repeat" >'
        self._test_one_link(content % url, url)
        content = "<table style='background: url( \"%s\") no-repeat' >"
        self._test_one_link(content % url, url)


def test_suite ():
    """
    Build and return a TestSuite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLinkparser))
    return suite

if __name__ == '__main__':
    unittest.main()
