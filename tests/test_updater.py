# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008-2010 Bastian Kleineidam
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
Test update check functionality.
"""

import unittest
from tests import need_network
import linkcheck.updater


class TestUpdater (unittest.TestCase):
    """Test update check."""

    @need_network
    def test_updater (self):
        res, url = linkcheck.updater.check_update()
        self.assertTrue(type(res) == bool)
        if res:
            self.assertTrue(url is None or isinstance(url, basestring))
        else:
            self.assertTrue(isinstance(url, unicode))
