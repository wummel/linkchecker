# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2009 Bastian Kleineidam
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
Test virus filter.
"""
import unittest
from tests import has_clamav
from nose import SkipTest
from linkcheck import clamav


class TestClamav (unittest.TestCase):

    def testClean (self):
        if not has_clamav():
            raise SkipTest("no ClamAV available")
        data = ""
        infected, errors = clamav.scan(data)
        self.assertFalse(infected)
        self.assertFalse(errors)

    def testInfected (self):
        if not has_clamav():
            raise SkipTest("no ClamAV available")
        data = '<object data="&#109;s-its:mhtml:file://'+ \
               'C:\\foo.mht!${PATH}/' + \
               'EXPLOIT.CHM::' + \
               '/exploit.htm">'
        infected, errors = clamav.scan(data)
        msg = 'stream: Exploit.HTML.MHTRedir.2n FOUND\n'
        self.assert_(msg in infected)
        self.assertFalse(errors)
