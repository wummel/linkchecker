# -*- coding: iso-8859-1 -*-
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
"""
Test url routines.
"""

import unittest
import os
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


def url_norm (url):
    return linkcheck.url.url_norm(url)[0]


class TestUrl (unittest.TestCase):
    """
    Test url norming and quoting.
    """

    def test_pathattack (self):
        """
        Windows winamp path attack prevention.
        """
        url = "http://server/..%5c..%5c..%5c..%5c..%5c..%5c..%5c.."\
              "%5ccskin.zip"
        nurl = "http://server/cskin.zip"
        self.assertEquals(linkcheck.url.url_quote(url_norm(url)), nurl)

    def test_norm_quote (self):
        """
        Test url norm quoting.
        """
        url = "http://groups.google.com/groups?hl=en&lr&ie=UTF-8&"\
              "threadm=3845B54D.E546F9BD%40monmouth.com&rnum=2&"\
              "prev=/groups%3Fq%3Dlogitech%2Bwingman%2Bextreme%2Bdigital"\
              "%2B3d%26hl%3Den%26lr%3D%26ie%3DUTF-8%26selm%3D3845B54D.E5"\
              "46F9BD%2540monmouth.com%26rnum%3D2"
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = "http://redirect.alexa.com/redirect?"\
              "http://www.offeroptimizer.com"
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = "http://www.lesgensducinema.com/photo/Philippe%20Nahon.jpg"
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        # Only perform percent-encoding where it is essential.
        url = "http://example.com/%7Ejane"
        nurl = "http://example.com/~jane"
        self.assertEqual(url_norm(url), nurl)
        url = "http://example.com/%7ejane"
        self.assertEqual(url_norm(url), nurl)
        # Always use uppercase A-through-F characters when percent-encoding.
        url = "http://example.com/?q=1%2a2"
        nurl = "http://example.com/?q=1%2A2"
        self.assertEqual(url_norm(url), nurl)
        # the no-quote chars
        url = "http://example.com/a*+-();b"
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = "http://www.company.com/path/doc.html?url=/path2/doc2.html?foo=bar"
        nurl = url
        self.assertEqual(url_norm(url), nurl)

    def test_norm_case_sensitivity (self):
        """
        Test url norm case sensitivity.
        """
        # Always provide the URI scheme in lowercase characters.
        url = "HTTP://example.com/"
        nurl = "http://example.com/"
        self.assertEqual(url_norm(url), nurl)
        # Always provide the host, if any, in lowercase characters.
        url = "http://EXAMPLE.COM/"
        nurl = "http://example.com/"
        self.assertEqual(url_norm(url), nurl)
        url = "http://EXAMPLE.COM:55/"
        nurl = "http://example.com:55/"
        self.assertEqual(url_norm(url), nurl)

    def test_norm_defaultport (self):
        """
        Test url norm default port recognition.
        """
        # For schemes that define a port, use an empty port if the default
        # is desired
        url = "http://example.com:80/"
        nurl = "http://example.com/"
        self.assertEqual(url_norm(url), nurl)
        url = "http://example.com:8080/"
        nurl = "http://example.com:8080/"
        self.assertEqual(url_norm(url), nurl)

    def test_norm_host_dot (self):
        """
        Test url norm host dot removal.
        """
        url = "http://example.com./"
        nurl = "http://example.com/"
        self.assertEqual(url_norm(url), nurl)
        url = "http://example.com.:81/"
        nurl = "http://example.com:81/"
        self.assertEqual(url_norm(url), nurl)

    def test_norm_fragment (self):
        """
        Test url norm fragment preserving.
        """
        # Empty fragment identifiers must be preserved:
        url = "http://www.w3.org/2000/01/rdf-schema#"
        nurl = url
        self.assertEqual(url_norm(url), nurl)

    def test_norm_empty_path (self):
        """
        Test url norm empty path handling.
        """
        # For schemes that define an empty path to be equivalent to a
        # path of "/", use "/".
        url = "http://example.com"
        nurl = "http://example.com/"
        self.assertEqual(url_norm(url), nurl)
        url = "http://example.com?a=b"
        nurl = "http://example.com/?a=b"
        self.assertEqual(url_norm(url), nurl)

    def test_norm_path_backslashes (self):
        """
        Test url norm backslash path handling.
        """
        # note: this is not RFC conform (see url.py for more info)
        url = r"http://example.com\test.html"
        nurl = "http://example.com/test.html"
        self.assertEqual(url_norm(url), nurl)
        url = r"http://example.com/a\test.html"
        nurl = "http://example.com/a/test.html"
        self.assertEqual(url_norm(url), nurl)
        url = r"http://example.com\a\test.html"
        nurl = "http://example.com/a/test.html"
        self.assertEqual(url_norm(url), nurl)
        url = r"http://example.com\a/test.html"
        nurl = "http://example.com/a/test.html"
        self.assertEqual(url_norm(url), nurl)

    def test_norm_path_slashes (self):
        """
        Test url norm slashes in path handling.
        """
        # reduce duplicate slashes
        url = "http://example.com//a/test.html"
        nurl = "http://example.com/a/test.html"
        self.assertEqual(url_norm(url), nurl)
        url = "http://example.com//a/b/"
        nurl = "http://example.com/a/b/"
        self.assertEqual(url_norm(url), nurl)

    def test_norm_path_dots (self):
        """
        Test url norm dots in path handling.
        """
        # Prevent dot-segments appearing in non-relative URI paths.
        url = "http://example.com/a/./b"
        nurl = "http://example.com/a/b"
        self.assertEqual(url_norm(url), nurl)
        url = "http://example.com/a/../a/b"
        self.assertEqual(url_norm(url), nurl)

    def test_norm_path_relative_dots (self):
        """
        Test url norm relative path handling with dots.
        """
        # normalize redundant path segments
        url = '/foo/bar/.'
        nurl = '/foo/bar/'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/bar/./'
        nurl = '/foo/bar/'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/bar/..'
        nurl = '/foo/'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/bar/../'
        nurl = '/foo/'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/bar/../baz'
        nurl = '/foo/baz'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/bar/../..'
        nurl = '/'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/bar/../../'
        nurl = '/'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/bar/../../baz'
        nurl = '/baz'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/bar/../../../baz'
        nurl = '/baz'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/bar/../../../../baz'
        nurl = '/baz'
        self.assertEqual(url_norm(url), nurl)
        url = '/./foo'
        nurl = '/foo'
        self.assertEqual(url_norm(url), nurl)
        url = '/../foo'
        nurl = '/foo'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo.'
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = '/.foo'
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = '/foo..'
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = '/..foo'
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = '/./../foo'
        nurl = '/foo'
        self.assertEqual(url_norm(url), nurl)
        url = '/./foo/.'
        nurl = '/foo/'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/./bar'
        nurl = '/foo/bar'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo/../bar'
        nurl = '/bar'
        self.assertEqual(url_norm(url), nurl)
        url = '../../../images/miniXmlButton.gif'
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = '/a..b/../images/miniXmlButton.gif'
        nurl = '/images/miniXmlButton.gif'
        self.assertEqual(url_norm(url), nurl)
        url = '/.a.b/../foo/'
        nurl = '/foo/'
        self.assertEqual(url_norm(url), nurl)
        url = '/..a.b/../foo/'
        nurl = '/foo/'
        self.assertEqual(url_norm(url), nurl)
        url = 'b/../../foo/'
        nurl = '../foo/'
        self.assertEqual(url_norm(url), nurl)

    def test_norm_path_relative_slashes (self):
        """
        Test url norm relative path handling with slashes.
        """
        url = '/foo//'
        nurl = '/foo/'
        self.assertEqual(url_norm(url), nurl)
        url = '/foo///bar//'
        nurl = '/foo/bar/'
        self.assertEqual(url_norm(url), nurl)

    def test_mail_url (self):
        """
        Test mailto urls.
        """
        # no netloc and no path
        url = 'mailto:'
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        # standard email
        url = 'mailto:user@www.imadoofus.org'
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        # email with subject
        url = 'mailto:user@www.imadoofus.org?subject=a_b'
        nurl = url
        self.assertEqual(url_norm(url), nurl)

    def test_norm_other (self):
        """
        Test norming of other schemes.
        """
        # using netloc
        # no netloc and no path
        url = 'news:'
        nurl = 'news:'
        self.assertEqual(url_norm(url), nurl)
        url = 'snews:'
        nurl = 'snews://'
        self.assertEqual(url_norm(url), nurl)
        # using netloc and path
        url = 'nntp:'
        nurl = 'nntp:///'
        self.assertEqual(url_norm(url), nurl)
        url = "news:§$%&/´`§%"
        nurl = 'news:%A7%24%25%26/%B4%60%A7%25'
        self.assertEqual(url_norm(url), nurl)
        # javascript url
        url = "javascript:loadthis()"
        nurl = url
        self.assertEqual(url_norm(url), nurl)

    def test_norm_with_auth (self):
        """
        Test norming of urls with authentication tokens.
        """
        url = "telnet://user@www.imadoofus.org"
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = "telnet://user:pass@www.imadoofus.org"
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        url = "http://user:pass@www.imadoofus.org/"
        nurl = url
        self.assertEqual(url_norm(url), nurl)

    def test_fixing (self):
        """
        Test url fix method.
        """
        url = "http//www.imadoofus.org"
        nurl = "http://www.imadoofus.org"
        self.assertEqual(linkcheck.url.url_fix_common_typos(url), nurl)
        url = u"http//www.imadoofus.org"
        nurl = u"http://www.imadoofus.org"
        self.assertEqual(linkcheck.url.url_fix_common_typos(url), nurl)

    def test_valid (self):
        """
        Test url validity functions.
        """
        u = "http://www.imadoofus.com"
        self.assert_(linkcheck.url.is_safe_url(u), u)
        u = "http://www.imadoofus.com/"
        self.assert_(linkcheck.url.is_safe_url(u), u)
        u = "http://www.imadoofus.com/~calvin"
        self.assert_(linkcheck.url.is_safe_url(u), u)
        u = "http://www.imadoofus.com/a,b"
        self.assert_(linkcheck.url.is_safe_url(u), u)
        u = "http://www.imadoofus.com#anchor55"
        self.assert_(linkcheck.url.is_safe_url(u), u)
        u = "http://www.imadoofus.com/?hulla=do"
        self.assert_(linkcheck.url.is_safe_js_url(u), u)
        u = "http://www.imadoofus.com/foo.bar/woot/bla;a=120x600;b=615660"
        self.assert_(linkcheck.url.is_safe_js_url(u), u)

    def test_needs_quoting (self):
        """
        Test url quoting necessity.
        """
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

    def test_nopathquote_chars (self):
        # XXX use platform resource
        if os.name != 'nt':
            return
        url = "file:///c|/msys/"
        nurl = url
        self.assertEqual(url_norm(url), nurl)
        self.assert_(not linkcheck.url.url_needs_quoting(url))

    def test_idn_encoding (self):
        """
        Test idna encoding.
        """
        url = u'www.öko.de'
        encurl, is_idn = linkcheck.url.idna_encode(url)
        self.assert_(is_idn)
        url = u''
        encurl, is_idn = linkcheck.url.idna_encode(url)
        self.assert_(not is_idn)
        self.assert_(not encurl)

    def test_match_host (self):
        """
        Test host matching.
        """
        self.assert_(not linkcheck.url.match_host("localhost", [".localhost"]))
        self.assert_(linkcheck.url.match_host("a.localhost", [".localhost"]))
        self.assert_(linkcheck.url.match_host("localhost", ["localhost"]))

    def test_splitparam (self):
        """
        Path parameter split test.
        """
        p = [
            ("", ("", "")),
            ("/", ("/", "")),
            ("a", ("a", "")),
            ("a;", ("a", "")),
            ("a/b;c/d;e", ("a/b;c/d", "e")),
        ]
        for x in p:
            self._splitparam(x)

    def _splitparam (self, x):
        self.assertEqual(linkcheck.url.splitparams(x[0]), (x[1][0], x[1][1]))


def test_suite ():
    """
    Build and return a TestSuite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUrl))
    return suite

if __name__ == '__main__':
    unittest.main()
