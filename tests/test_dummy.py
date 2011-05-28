# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2011 Bastian Kleineidam
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
Test dummy object.
"""

import unittest
import linkcheck.dummy


class TestDummy (unittest.TestCase):
    """
    Test dummy object.
    """

    def test_creation (self):
        dummy = linkcheck.dummy.Dummy()
        dummy = linkcheck.dummy.Dummy("1")
        dummy = linkcheck.dummy.Dummy("1", "2")
        dummy = linkcheck.dummy.Dummy(a=1, b=2)
        dummy = linkcheck.dummy.Dummy("1", a=None, b=2)

    def test_attributes (self):
        dummy = linkcheck.dummy.Dummy()
        dummy.hulla
        dummy.hulla.bulla
        dummy.hulla = 1
        del dummy.wulla
        del dummy.wulla.mulla

    def test_methods (self):
        dummy = linkcheck.dummy.Dummy()
        dummy.hulla()
        dummy.hulla().bulla()
        if "a" in dummy:
            pass

    def test_indexes (self):
        dummy = linkcheck.dummy.Dummy()
        len(dummy)
        dummy[1] = dummy[2]
        dummy[1][-1]
        dummy[1:3] = None
        del dummy[1]
        del dummy[2]
        del dummy[2:3]
        str(dummy)
        repr(dummy)
        unicode(dummy)
