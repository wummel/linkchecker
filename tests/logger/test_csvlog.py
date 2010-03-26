# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-2010 Bastian Kleineidam
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

import unittest
import os
from linkcheck.logger.csvlog import CSVLogger


class TestCsvLogger (unittest.TestCase):

    def test_parts (self):
        args = dict(
            filename=os.path.join(os.path.dirname(__file__), "testlog.csv"),
            parts=["realurl"],
            fileoutput=1,
            separator=";",
            quotechar='"',
        )
        logger = CSVLogger(**args)
        try:
            logger.start_output()
        finally:
            logger.end_output()
            os.remove(args["filename"])
