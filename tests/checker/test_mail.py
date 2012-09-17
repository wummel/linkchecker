# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2011 Bastian Kleineidam
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
Test mail checking.
"""
from tests import need_network
from . import LinkCheckTest


class TestMail (LinkCheckTest):
    """
    Test mailto: link checking.
    """

    @need_network
    def test_good_mail (self):
        # some good mailto addrs
        url = self.norm(u"mailto:Dude <calvin@users.sourceforge.net> , "\
                "Killer <calvin@users.sourceforge.net>?subject=bla")
        resultlines = [
          u"url %s" % url,
          u"cache key mailto:calvin@users.sourceforge.net",
          u"real url %s" % url,
          u"info Verified address calvin@users.sourceforge.net: 250 <calvin@users.sourceforge.net> is deliverable.",
          u"valid",
        ]
        self.direct(url, resultlines)
        url = self.norm(u"mailto:Bastian Kleineidam <calvin@users.sourceforge.net>?"\
                "bcc=calvin%40users.sourceforge.net")
        resultlines = [
          u"url %s" % url,
          u"cache key mailto:calvin@users.sourceforge.net",
          u"real url %s" % url,
          u"info Verified address calvin@users.sourceforge.net: 250 <calvin@users.sourceforge.net> is deliverable.",
          u"valid",
        ]
        self.direct(url, resultlines)
        url = self.norm(u"mailto:Bastian Kleineidam <calvin@users.sourceforge.net>")
        resultlines = [
            u"url %s" % url,
            u"cache key mailto:calvin@users.sourceforge.net",
            u"real url %s" % url,
            u"info Verified address calvin@users.sourceforge.net: 250 <calvin@users.sourceforge.net> is deliverable.",
            u"valid",
        ]
        self.direct(url, resultlines)
        url = self.norm(u"mailto:o'hara@users.sourceforge.net")
        resultlines = [
            u"url %s" % url,
            u"cache key mailto:o'hara@users.sourceforge.net",
            u"real url %s" % url,
            u"warning Unverified address: 550 <o'hara@users.sourceforge.net> Unrouteable address.",
            u"valid",
        ]
        self.direct(url, resultlines)
        url = self.norm(u"mailto:?to=calvin@users.sourceforge.net&subject=blubb&"
                       u"cc=calvin_cc@users.sourceforge.net&CC=calvin_CC@users.sourceforge.net")
        resultlines = [
            u"url %s" % url,
            u"cache key mailto:calvin@users.sourceforge.net,"
             u"calvin_CC@users.sourceforge.net,calvin_cc@users.sourceforge.net",
            u"real url %s" % url,
           u"info Verified address calvin@users.sourceforge.net: 250 <calvin@users.sourceforge.net> is deliverable.",
            u"warning Unverified address: 550 <calvin_CC@users.sourceforge.net> Unrouteable address.",
            u"warning Unverified address: 550 <calvin_cc@users.sourceforge.net> Unrouteable address.",
            u"valid",
        ]
        self.direct(url, resultlines)
        url = self.norm(u"mailto:news-admins@freecode.com?subject="
                "Re:%20[fm%20#11093]%20(news-admins)%20Submission%20"
                "report%20-%20Pretty%20CoLoRs")
        resultlines = [
            u"url %s" % url,
            u"cache key mailto:news-admins@freecode.com",
            u"real url %s" % url,
            u"warning Unverified address: 502 5.5.1 VRFY command is disabled.",
            u"valid",
        ]
        self.direct(url, resultlines)

    @need_network
    def test_warn_mail (self):
        # some mailto addrs with warnings
        # contains non-quoted characters
        url = u"mailto:calvin@users.sourceforge.net?subject=äöü"
        qurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key mailto:calvin@users.sourceforge.net",
            u"real url %s" % qurl,
            u"info Verified address calvin@users.sourceforge.net: 250 <calvin@users.sourceforge.net> is deliverable.",
            u"valid",
        ]
        self.direct(url, resultlines)
        url = u"mailto:calvin@users.sourceforge.net?subject=Halli hallo"
        qurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key mailto:calvin@users.sourceforge.net",
            u"real url %s" % qurl,
            u"info Verified address calvin@users.sourceforge.net: 250 <calvin@users.sourceforge.net> is deliverable.",
            u"valid",
        ]
        self.direct(url, resultlines)
        url = u"mailto:"
        resultlines = [
            u"url %s" % url,
            u"cache key mailto:",
            u"real url %s" % url,
            u"warning No mail addresses found in `%s'." % url,
            u"valid",
        ]
        self.direct(url, resultlines)

    def mail_valid (self, addr, **kwargs):
        return self.mail_test(addr, u"valid", **kwargs)

    def mail_error (self, addr, **kwargs):
        return self.mail_test(addr, u"error", **kwargs)

    def mail_test (self, addr, result, cache_key=None, warning=None):
        """Test error mails."""
        url = self.norm(addr)
        if cache_key is None:
            cache_key = url
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % cache_key,
            u"real url %s" % url,
        ]
        if warning:
            resultlines.append(u"warning %s" % warning)
        resultlines.append(result)
        self.direct(url, resultlines)

    def test_error_mail (self):
        # too long or too short
        self.mail_error(u"mailto:@")
        self.mail_error(u"mailto:@example.org")
        self.mail_error(u"mailto:a@")
        url_too_long = "URL length %d is longer than 255."
        url = u"mailto:%s@%s" % (u"a"*60, u"b"*200)
        warning = url_too_long % len(url)
        self.mail_error(url, warning=warning)
        url = u"mailto:a@%s" % (u"a"*256)
        warning = url_too_long % len(url)
        self.mail_error(url, warning=warning)
        self.mail_error(u"mailto:%s@example.org" % (u"a"*65))
        self.mail_error(u'mailto:a@%s.com' % (u"a"*64))
        # local part quoted
        self.mail_error(u'mailto:"a""@example.com', cache_key=u'mailto:a')
        self.mail_error(u'mailto:""a"@example.com', cache_key=u'mailto:""a"@example.com')
        self.mail_error(u'mailto:"a\\"@example.com', cache_key=u'mailto:a"@example.com')
        # local part unqouted
        self.mail_error(u'mailto:.a@example.com')
        self.mail_error(u'mailto:a.@example.com')
        self.mail_error(u'mailto:a..b@example.com')
        # domain part
        self.mail_error(u'mailto:a@a_b.com')
        self.mail_error(u'mailto:a@example.com.')
        self.mail_error(u'mailto:a@example.com.111')
        self.mail_error(u'mailto:a@example..com')
        # other
        # ? extension forbidden in <> construct
        self.mail_error(u"mailto:Bastian Kleineidam <calvin@users.sourceforge.net?foo=bar>",
            cache_key=u"mailto:calvin@users.sourceforge.net?foo=bar")

    @need_network
    def test_valid_mail (self):
        # valid mail addresses
        for char in u"!#$&'*+-/=^_`.{|}~":
            addr = u'abc%sdef@sourceforge.net' % char
            self.mail_valid(u"mailto:%s" % addr,
                warning=u"Unverified address: 550 <%s> Unrouteable address." % addr,
                cache_key=u"mailto:%s" % addr)

    @need_network
    def test_unicode_mail (self):
        mailto = u"mailto:ölvin@users.sourceforge.net"
        url = self.norm(mailto, encoding="iso-8859-1")
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % mailto,
            u"real url %s" % url,
            u"warning Unverified address: 550 <lvin@users.sourceforge.net> Unrouteable address.",
            u"valid",
        ]
        self.direct(url, resultlines)
