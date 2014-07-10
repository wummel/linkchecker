# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2014 Bastian Kleineidam
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
        h = linkparse.LinkFinder(self._test_one_url(url), linkparse.LinkTags)
        p = linkcheck.HtmlParser.htmlsax.parser(h)
        h.parser = p
        try:
            p.feed(content)
            p.flush()
        except linkparse.StopParse:
            pass
        h.parser = None
        p.handler = None
        self.assertEqual(self.count_url, 1)

    def _test_one_url (self, origurl):
        """Return parser callback function."""
        def callback (url, line, column, name, base):
            self.count_url += 1
            self.assertEqual(origurl, url)
        return callback

    def _test_no_link (self, content):
        def callback (url, line, column, name, base):
            self.assertTrue(False, 'URL %r found' % url)
        h = linkparse.LinkFinder(callback, linkparse.LinkTags)
        p = linkcheck.HtmlParser.htmlsax.parser(h)
        h.parser = p
        try:
            p.feed(content)
            p.flush()
        except linkparse.StopParse:
            pass
        h.parser = None
        p.handler = None

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

    def test_img_srcset_parsing(self):
        content = u'<img srcset="%s 1x">'
        url = u"imagesmall.jpg"
        self._test_one_link(content % url, url)

    def test_itemtype_parsing(self):
        content = u'<div itemtype="%s">'
        url = u"http://example.org/Movie"
        self._test_one_link(content % url, url)

    def test_form_parsing(self):
        # Test <form action> parsing
        content = u'<form action="%s">'
        url = u"alink"
        self._test_one_link(content % url, url)
        content = u'<form action="%s" method="POST">'
        url = u"alink"
        self._test_no_link(content % url)

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

    def test_url_quoting(self):
        url = u'http://example.com/bla/a=b'
        content = u'<a href="%s&quot;">'
        self._test_one_link(content % url, url + u'"')
