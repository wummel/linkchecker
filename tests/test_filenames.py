# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2014 Bastian Kleineidam
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
Test filename routines.
"""

import unittest
import os
from linkcheck.checker.fileurl import get_nt_filename
from . import need_windows


class TestFilenames (unittest.TestCase):
    """
    Test filename routines.
    """

    @need_windows
    def test_nt_filename (self):
        path = os.getcwd()
        realpath = get_nt_filename(path)
        self.assertEqual(path, realpath)
        path = 'c:\\'
        realpath = get_nt_filename(path)
        self.assertEqual(path, realpath)
        # XXX Only works on my computer.
        # Is there a Windows UNC share that is always available for tests?
        #path = '\\Vboxsrv\share\msg.txt'
        #realpath = get_nt_filename(path)
        #self.assertEqual(path, realpath)
