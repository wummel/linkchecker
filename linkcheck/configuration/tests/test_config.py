# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006 Bastian Kleineidam
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
Test config parsing.
"""

import unittest
import os
import linkcheck.configuration


def get_file (filename=None):
    """
    Get file name located within 'data' directory.
    """
    directory = os.path.join("linkcheck", "configuration", "tests", "data")
    if filename:
        return unicode(os.path.join(directory, filename))
    return unicode(directory)


class TestConfig (unittest.TestCase):
    """
    Test cgi routines.
    """

    def test_confparse (self):
        """
        Check url validity.
        """
        config = linkcheck.configuration.Configuration()
        files = [get_file("config1.ini")]
        config.read(files)


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestConfig)


if __name__ == '__main__':
    unittest.main()
