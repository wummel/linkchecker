#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2009 Bastian Kleineidam
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

import sys
import cgi
import linkcheck
import linkcheck.lc_cgi

# log errors to stdout
sys.stderr = sys.stdout

# uncomment the following lines to test your CGI values
#cgi.test()
#sys.exit(0)
linkcheck.lc_cgi.startoutput()
linkcheck.lc_cgi.checklink(form=cgi.FieldStorage())
