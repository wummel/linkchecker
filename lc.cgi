#!/usr/bin/python
# Copyright (C) 2000-2002  Bastian Kleineidam
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

import re, cgi, sys, urlparse, time, os
# log errors to stdout
sys.stderr = sys.stdout

# access
ALLOWED_HOSTS = ['127.0.0.1']
ALLOWED_SERVERS = ['127.0.0.1']
# uncomment the following lines to test your CGI values
#cgi.test()
#sys.exit(0)
import linkcheck.lc_cgi
linkcheck.lc_cgi.checkaccess(hosts=ALLOWED_HOSTS, servers=ALLOWED_SERVERS)
linkcheck.lc_cgi.checklink(form=cgi.FieldStorage())
