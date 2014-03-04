# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2014 Bastian Kleineidam
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
Test robots.txt parsing.
"""

import unittest
import linkcheck.robotparser2


class TestRobotsTxt (unittest.TestCase):
    """
    Test string formatting routines.
    """

    def setUp (self):
        """
        Initialize self.rp as a robots.txt parser.
        """
        self.rp = linkcheck.robotparser2.RobotFileParser()

    def test_robotstxt (self):
        lines = [
            "User-agent: *",
        ]
        self.rp.parse(lines)
        self.assertTrue(self.rp.mtime() > 0)
        self.assertEqual(str(self.rp), "\n".join(lines))

    def test_robotstxt2 (self):
        lines = [
            "User-agent: *",
            "Disallow: /search",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "\n".join(lines))

    def test_robotstxt3 (self):
        lines = [
            "Disallow: /search",
            "",
            "Allow: /search",
            "",
            "Crawl-Delay: 5",
            "",
            "Blabla",
            "",
            "Bla: bla",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "")

    def test_robotstxt4 (self):
        lines = [
            "User-agent: Bla",
            "Disallow: /cgi-bin",
            "User-agent: *",
            "Disallow: /search",
        ]
        self.rp.parse(lines)
        lines.insert(2, "")
        self.assertEqual(str(self.rp), "\n".join(lines))

    def test_robotstxt5 (self):
        lines = [
            "#one line comment",
            "User-agent: Bla",
            "Disallow: /cgi-bin # comment",
            "Allow: /search",
        ]
        lines2 = [
            "User-agent: Bla",
            "Disallow: /cgi-bin",
            "Allow: /search",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "\n".join(lines2))

    def test_robotstxt6 (self):
        lines = [
            "User-agent: Bla",
            "",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "")

    def test_robotstxt7 (self):
        lines = [
            "User-agent: Bla",
            "Allow: /",
            "",
            "User-agent: *",
            "Disallow: /",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "\n".join(lines))
        self.assertTrue(self.rp.can_fetch("Bla", "/"))

    def test_crawldelay (self):
        lines = [
            "User-agent: Blubb",
            "Crawl-delay: 10",
            "",
            "User-agent: Hulla",
            "Crawl-delay: 5",
            "",
            "User-agent: *",
            "Crawl-delay: 1",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "\n".join(lines))
        self.assertEqual(self.rp.get_crawldelay("Blubb"), 10)
        self.assertEqual(self.rp.get_crawldelay("Hulla"), 5)
        self.assertEqual(self.rp.get_crawldelay("Bulla"), 1)

    def test_crawldelay2 (self):
        lines = [
            "User-agent: Blubb",
            "Crawl-delay: X",
        ]
        self.rp.parse(lines)
        del lines[1]
        self.assertEqual(str(self.rp), "\n".join(lines))

    def check_urls (self, good, bad, agent="test_robotparser"):
        for url in good:
            self.check_url(agent, url, True)
        for url in bad:
            self.check_url(agent, url, False)

    def check_url (self, agent, url, can_fetch):
        if isinstance(url, tuple):
            agent, url = url
        res = self.rp.can_fetch(agent, url)
        if can_fetch:
            self.assertTrue(res, "%s disallowed" % url)
        else:
            self.assertFalse(res, "%s allowed" % url)

    def test_access1 (self):
        lines = [
            "User-agent: *",
            "Disallow: /cyberworld/map/ # This is an infinite virtual URL space",
            "Disallow: /tmp/ # these will soon disappear",
            "Disallow: /foo.html",
        ]
        lines2 = [
            "User-agent: *",
            "Disallow: /cyberworld/map/",
            "Disallow: /tmp/",
            "Disallow: /foo.html",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "\n".join(lines2))
        good = ['/', '/test.html']
        bad = ['/cyberworld/map/index.html', '/tmp/xxx', '/foo.html']
        self.check_urls(good, bad)

    def test_access2 (self):
        lines = [
            "# robots.txt for http://www.example.com/",
            "",
            "User-agent: *",
            "Disallow: /cyberworld/map/ # This is an infinite virtual URL space",
            "",
            "# Cybermapper knows where to go.",
            "User-agent: cybermapper",
            "Disallow:",
            "",
        ]
        lines2 = [
            "User-agent: cybermapper",
            "Allow: /",
            "",
            "User-agent: *",
            "Disallow: /cyberworld/map/",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "\n".join(lines2))
        good = ['/', '/test.html', ('cybermapper', '/cyberworld/map/index.html')]
        bad = ['/cyberworld/map/index.html']
        self.check_urls(good, bad)

    def test_access3 (self):
        lines = [
            "# go away",
            "User-agent: *",
            "Disallow: /",
        ]
        lines2 = [
            "User-agent: *",
            "Disallow: /",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "\n".join(lines2))
        good = []
        bad = ['/cyberworld/map/index.html', '/', '/tmp/']
        self.check_urls(good, bad)

    def test_access4 (self):
        lines = [
            "User-agent: figtree",
            "Disallow: /tmp",
            "Disallow: /a%3cd.html",
            "Disallow: /a%2fb.html",
            "Disallow: /%7ejoe/index.html",
        ]
        lines2 = [
            "User-agent: figtree",
            "Disallow: /tmp",
            "Disallow: /a%3Cd.html",
            "Disallow: /a/b.html",
            "Disallow: /%7Ejoe/index.html",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "\n".join(lines2))
        good = []
        bad = ['/tmp', '/tmp.html', '/tmp/a.html',
               '/a%3cd.html', '/a%3Cd.html', '/a%2fb.html',
               '/~joe/index.html', '/a/b.html',
        ]
        self.check_urls(good, bad, 'figtree')
        self.check_urls(good, bad, 'FigTree/1.0 Robot libwww-perl/5.04')

    def test_access5 (self):
        lines = [
            "User-agent: *",
            "Disallow: /tmp/",
            "Disallow: /a%3Cd.html",
            "Disallow: /a/b.html",
            "Disallow: /%7ejoe/index.html",
        ]
        lines2 = [
            "User-agent: *",
            "Disallow: /tmp/",
            "Disallow: /a%3Cd.html",
            "Disallow: /a/b.html",
            "Disallow: /%7Ejoe/index.html",
        ]
        self.rp.parse(lines)
        self.assertEqual(str(self.rp), "\n".join(lines2))
        good = ['/tmp'] # XFAIL: '/a%2fb.html'
        bad = ['/tmp/', '/tmp/a.html',
               '/a%3cd.html', '/a%3Cd.html', "/a/b.html",
               '/%7Ejoe/index.html']
        self.check_urls(good, bad)

    def test_access6 (self):
        lines = [
            "User-Agent: *",
            "Disallow: /.",
        ]
        self.rp.parse(lines)
        good = ['/foo.html']
        bad = [] # Bug report says "/" should be denied, but that is not in the RFC
        self.check_urls(good, bad)

    def test_access7 (self):
        lines = [
            "User-agent: Example",
            "Disallow: /example",
            "",
            "User-agent: *",
            "Disallow: /cgi-bin",
        ]
        self.rp.parse(lines)
        # test re.escape
        self.check_url("*", "/", True)
        # should match first agent
        self.check_url("", "/example", False)
        # test agent matching
        self.check_url("Example", "/example", False)
        self.check_url("Example/1.0", "/example", False)
        self.check_url("example", "/example", False)
        self.check_url("spam", "/cgi-bin", False)
        self.check_url("spam", "/cgi-bin/foo/bar", False)
        self.check_url("spam", "/cgi-bin?a=1", False)
        self.check_url("spam", "/", True)

    def test_sitemap(self):
        lines = [
            "Sitemap: bla",
        ]
        self.rp.parse(lines)
        self.assertTrue(len(self.rp.sitemap_urls) > 0)
        self.assertTrue(self.rp.sitemap_urls[0] == ("bla", 1))
