#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2007 Bastian Kleineidam
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
"""print headers of an url"""

import httplib
import urlparse
import sys

def main (url):
    parts = urlparse.urlsplit(url)
    host = parts[1]
    path = urlparse.urlunsplit(('', '', parts[2], parts[3], parts[4]))
    h = httplib.HTTPConnection(host)
    h.set_debuglevel(1)
    h.connect()
    h.putrequest("HEAD", path, skip_host=True)
    h.putheader("Host", host)
    h.putheader("User-Agent", "linkchecker")
    h.endheaders()
    req = h.getresponse()
    print req.msg


if __name__=='__main__':
    main(sys.argv[1])
