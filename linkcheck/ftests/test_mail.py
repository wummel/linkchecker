# -*- coding: iso-8859-1 -*-
"""test mail checking"""
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
import urllib
import os

import linkcheck.ftests

class TestMail (linkcheck.ftests.StandardTest):
    """test mailto: link checking"""

    def test_good_mail (self):
        """test some good mailto addrs"""
        url = self.quote("mailto:Dude <calvin@users.sf.net> , "\
                "Killer <calvin@users.sourceforge.net>?subject=bla")
        resultlines = [
            "url %s" % url,
            "info Verified adress: <calvin> is deliverable",
            "valid",
        ]
        self.direct(url, resultlines)
        url = self.quote("mailto:Bastian Kleineidam <calvin@users.sf.net>?"\
                "bcc=calvin%40users.sf.net")
        resultlines = [
            "url %s" % url,
            "info Verified adress: <calvin> is deliverable",
            "valid",
        ]
        self.direct(url, resultlines)
        url = self.quote("mailto:Bastian Kleineidam <calvin@users.sf.net>")
        resultlines = [
            "url %s" % url,
            "info Verified adress: <calvin> is deliverable",
            "valid",
        ]
        self.direct(url, resultlines)
        url = self.quote("mailto:o'hara@users.sf.net")
        resultlines = [
            "url %s" % url,
            "info Verified adress: <o'hara> is deliverable",
            "valid",
        ]
        self.direct(url, resultlines)
        url = self.quote("mailto:?to=calvin@users.sf.net&subject=blubb&"\
                "cc=calvin_cc@users.sf.net&CC=calvin_CC@users.sf.net")
        resultlines = [
            "url %s" % url,
            "info Verified adress: <calvin> is deliverable",
            "info Verified adress: <calvin_cc> is deliverable",
            "info Verified adress: <calvin_CC> is deliverable",
            "valid",
        ]
        self.direct(url, resultlines)
        url = self.quote("mailto:news-admins@freshmeat.net?subject="\
                "Re:%20[fm%20#11093]%20(news-admins)%20Submission%20"\
                "report%20-%20Pretty%20CoLoRs")
        resultlines = ["url %s" % url, "valid"]
        self.direct(url, resultlines)
        url = self.quote("mailto:"+"foo@foo-bar.de?subject=test")
        resultlines = ["url %s" % url, "valid"]
        self.direct(url, resultlines)

    def test_warn_mail (self):
        """test some mailto addrs with warnings"""
        # contains non-quoted characters
        url = "calvin@users.sf.net?subject=äöü"
        resultlines = [
            "url %s" % self.quote("mailto:"+url),
            "info Verified adress: <calvin> is deliverable",
            "warning Base URL is not properly quoted",
            "valid",
        ]
        self.direct("mailto:"+url, resultlines)
        url = "calvin@users.sf.net?subject=Halli hallo"
        resultlines = [
            "url %s" % self.quote("mailto:"+url),
            "info Verified adress: <calvin> is deliverable",
            "warning Base URL is not properly quoted",
            "valid",
        ]
        self.direct("mailto:"+url, resultlines)
        url = self.quote("mailto:")
        resultlines = [
            "url %s" % url,
            "warning No adresses found",
            "valid",
        ]
        self.direct(url, resultlines)

    def test_bad_mail (self):
        """test some mailto addrs with bad syntax"""
        # ? extension forbidden in <> construct
        url = self.quote("mailto:Bastian Kleineidam "\
                         "<calvin@users.sf.net?foo=bar>")
        resultlines = ["url %s" % url, "error"]
        self.direct(url, resultlines)


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMail))
    return suite


if __name__ == '__main__':
    unittest.main()
