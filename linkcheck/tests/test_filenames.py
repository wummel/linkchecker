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
Test filename routines.
"""

import unittest
import os
from linkcheck.checker.fileurl import get_nt_filename


class TestFilenames (unittest.TestCase):
    """
    Test filename routines.
    """

    def test_nt_filename (self):
        path = os.getcwd()
        realpath = get_nt_filename(path)
        self.assertEquals(path, realpath)
        if os.name == 'nt':
            path = 'c:\\'
            realpath = get_nt_filename(path)
            self.assertEquals(path, realpath)


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestFilenames)


if __name__ == '__main__':
    unittest.main()
