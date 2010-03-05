# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2010 Bastian Kleineidam
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
Test decorators.
"""

import unittest
import time
from cStringIO import StringIO
import linkcheck.decorators


class TestDecorators (unittest.TestCase):
    """
    Test decorators.
    """

    def test_timeit (self):
        @linkcheck.decorators.timed()
        def f ():
            return 42
        self.assertEqual(f(), 42)

    def test_timeit2 (self):
        log = StringIO()
        @linkcheck.decorators.timed(log=log, limit=0)
        def f ():
            time.sleep(1)
            return 42
        self.assertEqual(f(), 42)
        self.assertTrue(log.getvalue())
