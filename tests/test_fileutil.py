# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2014 Bastian Kleineidam
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
Test file utility functions.
"""

import unittest
import linkcheck.fileutil

file_existing = __file__
file_non_existing = "ZZZ.i_dont_exist"


class TestFileutil (unittest.TestCase):
    """Test file utility functions."""

    def test_size (self):
        self.assertTrue(linkcheck.fileutil.get_size(file_existing) > 0)
        self.assertEqual(linkcheck.fileutil.get_size(file_non_existing), -1)

    def test_mtime (self):
        self.assertTrue(linkcheck.fileutil.get_mtime(file_existing) > 0)
        self.assertEqual(linkcheck.fileutil.get_mtime(file_non_existing), 0)
