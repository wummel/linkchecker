# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2010 Bastian Kleineidam
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
Test linkparser routines.
"""

import unittest
from linkcheck.htmlutil import linkparse
import linkcheck.HtmlParser.htmlsax


class TestLinkparser (unittest.TestCase):
    """
    Test link parsing.
    """

    def _test_one_link (self, content, url):
        self.count_url = 0
        h = linkparse.LinkFinder(content, self._test_one_url(url))
        p = linkcheck.HtmlParser.htmlsax.parser(h)
        h.parser = p
        try:
            p.feed(content)
            p.flush()
        except linkparse.StopParse:
            pass
        h.parser = None
        p.handler = None

    def _test_one_url (self, origurl):
        """Return parser callback function."""
        def callback (url, line, column, name, base):
            self.count_url += 1
            self.assertEqual(self.count_url, 1)
            self.assertEqual(origurl, url)
        return callback

    def test_href_parsing (self):
        # Test <a href> parsing.
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
        # Test css style attribute parsing.
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
        strip = linkparse.strip_c_comments
        content = "/* url('http://example.org')*/"
        self.assertEqual(strip(content), "")
        content = "/* * * **/"
        self.assertEqual(strip(content), "")
        content = "/* * /* * **//* */"
        self.assertEqual(strip(content), "")
        content = "a/* */b/* */c"
        self.assertEqual(strip(content), "abc")
