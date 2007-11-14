# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2007 Bastian Kleineidam
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
        self.assertEqual(len(h.urls), 0)
        p = linkcheck.HtmlParser.htmlsax.parser(h)
        h.parser = p
        p.feed(content)
        p.flush()
        h.parser = None
        p.handler = None
        self.assertEqual(len(h.urls), 1)
        purl = h.urls[0][0]
        self.assertEqual(purl, url)

    def test_href_parsing (self):
        """
        Test <a href> parsing.
        """
        content = u'<a href="%s">'
        url = u"alink"
        self._test_one_link(content % url, url)
        url = u" alink"
        self._test_one_link(content % url, url)
        url = u"alink "
        self._test_one_link(content % url, url)
        url = u" alink "
        self._test_one_link(content % url, url)

    def test_css_parsing (self):
        """
        Test css style attribute parsing.
        """
        content = u'<table style="background: url(%s) no-repeat" >'
        url = u"alink"
        self._test_one_link(content % url, url)
        content = u'<table style="background: url(%s) no-repeat" >'
        self._test_one_link(content % url, url)
        content = u'<table style="background: url(%s ) no-repeat" >'
        self._test_one_link(content % url, url)
        content = u'<table style="background: url( %s ) no-repeat" >'
        self._test_one_link(content % url, url)
        content = u'<table style="background: url(\'%s\') no-repeat" >'
        self._test_one_link(content % url, url)
        content = u"<table style='background: url(\"%s\") no-repeat' >"
        self._test_one_link(content % url, url)
        content = u'<table style="background: url(\'%s\' ) no-repeat" >'
        self._test_one_link(content % url, url)
        content = u"<table style='background: url( \"%s\") no-repeat' >"
        self._test_one_link(content % url, url)

    def test_comment_stripping (self):
        strip = linkcheck.linkparse.strip_c_comments
        content = "/* url('http://imadoofus.org')*/"
        self.assertEqual(strip(content), "")
        content = "/* * * **/"
        self.assertEqual(strip(content), "")
        content = "/* * /* * **//* */"
        self.assertEqual(strip(content), "")
        content = "a/* */b/* */c"
        self.assertEqual(strip(content), "abc")


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestLinkparser)


if __name__ == '__main__':
    unittest.main()
