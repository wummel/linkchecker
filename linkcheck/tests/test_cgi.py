# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2006 Bastian Kleineidam
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
Test cgi form routines.
"""

import unittest
import tests
import linkcheck.lc_cgi


class Store (object):
    """
    Value storing class implementing FieldStorage interface.
    """

    def __init__ (self, value):
        """
        Store given value.
        """
        self.value = value


class TestCgi (tests.StandardTest):
    """
    Test cgi routines.
    """

    def test_form_valid_url (self):
        """
        Check url validity.
        """
        form = {"url": Store("http://www.heise.de/"),
                "level": Store("0"),
               }
        linkcheck.lc_cgi.checkform(form)

    def test_form_empty_url (self):
        """
        Check with empty url.
        """
        form = {"url": Store(""),
                "level": Store("0"),
               }
        self.assertRaises(linkcheck.lc_cgi.FormError,
                          linkcheck.lc_cgi.checkform, form)

    def test_form_default_url (self):
        """
        Check with default url.
        """
        form = {"url": Store("http://"),
                "level": Store("0"),
               }
        self.assertRaises(linkcheck.lc_cgi.FormError,
                          linkcheck.lc_cgi.checkform, form)

    def test_form_invalid_url (self):
        """
        Check url (in)validity.
        """
        form = {"url": Store("http://www.foo bar/"),
                "level": Store("0"),
               }
        self.assertRaises(linkcheck.lc_cgi.FormError,
                          linkcheck.lc_cgi.checkform, form)

def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestCgi)


if __name__ == '__main__':
    unittest.main()
