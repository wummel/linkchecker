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
Test url build method from url data objects.
"""

import unittest
import linkcheck.configuration
import linkcheck.checker.httpurl
import linkcheck.checker.cache
import linkcheck.checker.consumer

def get_test_consumer ():
    """
    Initialize a test configuration object.
    """
    config = linkcheck.configuration.Configuration()
    cache = linkcheck.checker.cache.Cache()
    return linkcheck.checker.consumer.Consumer(config, cache)


class TestUrlBuild (unittest.TestCase):
    """
    Test url building.
    """

    def test_http_build (self):
        parent_url = "http://localhost:8001/linkcheck/ftests/data/http.html"
        base_url = "http://"
        recursion_level = 0
        consumer = get_test_consumer()
        o = linkcheck.checker.httpurl.HttpUrl(base_url, recursion_level,
               consumer, parent_url=parent_url)
        o.build_url()
        self.assertEquals(o.url, 'http:///')


def test_suite ():
    """
    Build and return a TestSuite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUrlBuild))
    return suite

if __name__ == '__main__':
    unittest.main()
