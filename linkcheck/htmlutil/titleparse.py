# -*- coding: iso-8859-1 -*-
# Copyright (C) 2001-2008 Bastian Kleineidam
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
Find title tags in HTML text.
"""

from .. import log, LOG_CHECK
from . import linkname

MAX_TITLELEN = 256


class TitleFinder (object):

    def __init__ (self, content):
        """Initialize flags."""
        super(TitleFinder, self).__init__()
        log.debug(LOG_CHECK, "HTML title parser")
        self.content = content
        self.title = None

    def start_element (self, tag, attrs):
        """Search for meta robots.txt "nofollow" and "noindex" flags."""
        if tag == 'title':
            pos = self.parser.pos()
            data = self.content[pos:pos+MAX_TITLELEN]
            data = data.decode(self.parser.encoding, "ignore")
            self.title = linkname.title_name(data)
