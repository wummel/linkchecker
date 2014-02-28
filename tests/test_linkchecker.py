# -*- coding: utf-8 -*-
# Copyright (C) 2014 Bastian Kleineidam
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import sys
from . import linkchecker_cmd, run_checked


def run_with_options(options, cmd=linkchecker_cmd):
    """Run a command with given options."""
    run_checked([sys.executable, cmd] + options)


class TestLinkchecker (unittest.TestCase):
    """Test the linkchecker commandline client."""

    def test_linkchecker(self):
        # test some single options
        for option in ("-V", "--version", "-h", "--help", "--list-plugins", "-Dall"):
            run_with_options([option])
        # unknown option
        self.assertRaises(OSError, run_with_options, ['--imadoofus'])
