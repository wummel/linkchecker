# -*- coding: iso-8859-1 -*-
# Copyright (C) 2007 Bastian Kleineidam
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
Test internal pattern construction
"""

import unittest
import linkcheck.director
import linkcheck.configuration
from __init__ import LinkCheckTest, get_url_from


class TestInternpat (LinkCheckTest):
    """Test internal pattern."""

    def test_trailing_slash (self):
        """Make sure a trailing slash is not lost."""
        config = linkcheck.configuration.Configuration()
        aggregate = linkcheck.director.get_aggregate(config)
        url = "http://imadoofus.org/foo/"
        url_data = get_url_from(url, 0, aggregate)
        internpat = url_data.get_intern_pattern()
        self.assertTrue(internpat.endswith('/'))


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestInternpat)


if __name__ == '__main__':
    unittest.main()
