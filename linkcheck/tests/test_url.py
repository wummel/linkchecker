# -*- coding: iso-8859-1 -*-
"""test url routines"""
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
import linkcheck.url

# 'ftp://user:pass@ftp.foo.net/foo/bar':
#     'ftp://user:pass@ftp.foo.net/foo/bar',
# 'http://USER:pass@www.Example.COM/foo/bar':
#     'http://USER:pass@www.example.com/foo/bar',
# '-':                             '-',

# All portions of the URI must be utf-8 encoded NFC form Unicode strings
#valid:  http://example.com/?q=%C3%87   (C-cedilla U+00C7)
#valid: http://example.com/?q=%E2%85%A0 (Roman numeral one U+2160)
#invalid: http://example.com/?q=%C7      (C-cedilla ISO-8859-1)
#invalid: http://example.com/?q=C%CC%A7
#         (Latin capital letter C + Combining cedilla U+0327)


class TestUrl (unittest.TestCase):
    """test url norming and quoting"""

    def test_pathattack (self):
        """windows winamp path attack prevention"""
        url = "http://server/..%5c..%5c..%5c..%5c..%5c..%5c..%5c.."\
              "%5ccskin.zip"
        nurl = "http://server/cskin.zip"
        self.assertEquals(
                  linkcheck.url.url_quote(linkcheck.url.url_norm(url)), nurl)

    def test_norm_quote (self):
        """test url norm quoting"""
        url = "http://groups.google.com/groups?hl=en&lr&ie=UTF-8&"\
              "threadm=3845B54D.E546F9BD%40monmouth.com&rnum=2&"\
              "prev=/groups%3Fq%3Dlogitech%2Bwingman%2Bextreme%2Bdigital"\
              "%2B3d%26hl%3Den%26lr%3D%26ie%3DUTF-8%26selm%3D3845B54D.E5"\
              "46F9BD%2540monmouth.com%26rnum%3D2"
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "http://redirect.alexa.com/redirect?"\
              "http://www.offeroptimizer.com"
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "http://www.lesgensducinema.com/photo/Philippe%20Nahon.jpg"
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        # Only perform percent-encoding where it is essential.
        url = "http://example.com/%7Ejane"
        nurl = "http://example.com/~jane"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "http://example.com/%7ejane"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        # Always use uppercase A-through-F characters when percent-encoding.
        url = "http://example.com/?q=1%2a2"
        nurl = "http://example.com/?q=1%2A2"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        # the no-quote chars
        url = "http://example.com/a*+-();b"
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_case_sensitivity (self):
        """test url norm case sensitivity"""
        # Always provide the URI scheme in lowercase characters.
        url = "HTTP://example.com/"
        nurl = "http://example.com/"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        # Always provide the host, if any, in lowercase characters.
        url = "http://EXAMPLE.COM/"
        nurl = "http://example.com/"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "http://EXAMPLE.COM:55/"
        nurl = "http://example.com:55/"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_defaultport (self):
        """test url norm default port recognition"""
        # For schemes that define a port, use an empty port if the default
        # is desired
        url = "http://example.com:80/"
        nurl = "http://example.com/"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "http://example.com:8080/"
        nurl = "http://example.com:8080/"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_host_dot (self):
        """test url norm host dot removal"""
        url = "http://example.com./"
        nurl = "http://example.com/"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "http://example.com.:81/"
        nurl = "http://example.com:81/"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_fragment (self):
        """test url norm fragment preserving"""
        # Empty fragment identifiers must be preserved:
        url = "http://www.w3.org/2000/01/rdf-schema#"
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_path (self):
        """test url norm empty path handling"""
        # For schemes that define an empty path to be equivalent to a
        # path of "/", use "/".
        url = "http://example.com"
        nurl = "http://example.com/"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_path_backslashes (self):
        """test url norm backslash path handling"""
        # note: yes, this is not rfc conform (see url.py for more details)
        url = r"http://example.com\test.html"
        nurl = "http://example.com/test.html"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = r"http://example.com/a\test.html"
        nurl = "http://example.com/a/test.html"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = r"http://example.com\a\test.html"
        nurl = "http://example.com/a/test.html"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = r"http://example.com\a/test.html"
        nurl = "http://example.com/a/test.html"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_path_slashes (self):
        """test url norm slashes in path handling"""
        # reduce duplicate slashes
        url = "http://example.com//a/test.html"
        nurl = "http://example.com/a/test.html"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "http://example.com//a/b/"
        nurl = "http://example.com/a/b/"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_path_dots (self):
        """test url norm dots in path handling"""
        # Prevent dot-segments appearing in non-relative URI paths.
        url = "http://example.com/a/./b"
        nurl = "http://example.com/a/b"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "http://example.com/a/../a/b"
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_path_relative (self):
        """test url norm relative path handling"""
        # normalize redundant path segments
        url = '/foo/bar/.'
        nurl = '/foo/bar/'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/bar/./'
        nurl = '/foo/bar/'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/bar/..'
        nurl = '/foo/'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/bar/../'
        nurl = '/foo/'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/bar/../baz'
        nurl = '/foo/baz'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/bar/../..'
        nurl = '/'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/bar/../../'
        nurl = '/'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/bar/../../baz'
        nurl = '/baz'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/bar/../../../baz'
        nurl = '/baz'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/bar/../../../../baz'
        nurl = '/baz'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/./foo'
        nurl = '/foo'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/../foo'
        nurl = '/foo'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo.'
        nurl = '/foo.'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/.foo'
        nurl = '/.foo'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo..'
        nurl = '/foo..'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/..foo'
        nurl = '/..foo'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/./../foo'
        nurl = '/foo'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/./foo/.'
        nurl = '/foo/'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/./bar'
        nurl = '/foo/bar'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo/../bar'
        nurl = '/bar'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo//'
        nurl = '/foo/'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = '/foo///bar//'
        nurl = '/foo/bar/'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_other (self):
        """test norming of other schemes"""
        # no netloc and no path
        url = 'mailto:'
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        # standard email
        url = 'mailto:user@www.imadoofus.org'
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        # no netloc and no path
        url = 'news:'
        nurl = 'news:'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        # using netloc
        url = 'snews:'
        nurl = 'snews://'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        # using netloc and path
        url = 'nntp:'
        nurl = 'nntp:///'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "news:§$%&/´`§%"
        nurl = 'news:%A7%24%25%26/%B4%60%A7%25'
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        # javascript url
        url = "javascript:loadthis()"
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_norm_with_auth (self):
        """test norming of urls with authentication tokens"""
        url = "telnet://user@www.imadoofus.org"
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "telnet://user:pass@www.imadoofus.org"
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)
        url = "http://user:pass@www.imadoofus.org/"
        nurl = url
        self.assertEqual(linkcheck.url.url_norm(url), nurl)

    def test_valid (self):
        """test url validity functions"""
        self.assert_(linkcheck.url.is_safe_url("http://www.imadoofus.com"))
        self.assert_(linkcheck.url.is_safe_url("http://www.imadoofus.com/"))
        self.assert_(linkcheck.url.is_safe_url(
                                         "http://www.imadoofus.com/~calvin"))
        self.assert_(linkcheck.url.is_safe_url(
                                             "http://www.imadoofus.com/a,b"))
        self.assert_(linkcheck.url.is_safe_url(
                                        "http://www.imadoofus.com#anchor55"))
        self.assert_(linkcheck.url.is_safe_js_url(
                                       "http://www.imadoofus.com/?hulla=do"))

    def test_needs_quoting (self):
        """test url quoting necessity"""
        url = "mailto:<calvin@debian.org>?subject=Halli Hallo"
        self.assert_(linkcheck.url.url_needs_quoting(url), repr(url))
        url = " http://www.imadoofus.com/"
        self.assert_(linkcheck.url.url_needs_quoting(url), repr(url))
        url = "http://www.imadoofus.com/ "
        self.assert_(linkcheck.url.url_needs_quoting(url), repr(url))
        url = "http://www.imadoofus.com/\n"
        self.assert_(linkcheck.url.url_needs_quoting(url), repr(url))
        url = "\nhttp://www.imadoofus.com/"
        self.assert_(linkcheck.url.url_needs_quoting(url), repr(url))

    def test_absolute_url (self):
        url = "hutzli:"
        self.assert_(linkcheck.url.url_is_absolute(url), repr(url))
        url = "file:/"
        self.assert_(linkcheck.url.url_is_absolute(url), repr(url))
        url = ":"
        self.assert_(not linkcheck.url.url_is_absolute(url), repr(url))
        url = "/a/b?http://"
        self.assert_(not linkcheck.url.url_is_absolute(url), repr(url))

def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUrl))
    return suite

if __name__ == '__main__':
    unittest.main()
