# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2005  Bastian Kleineidam
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
Handle https links.
"""

import httpurl

class HttpsUrl (httpurl.HttpUrl):
    """
    Url link with https scheme.
    """

    def local_check (self):
        """
        Check connection if SSL is supported, else ignore.
        """
        if httpurl.supportHttps:
            super(HttpsUrl, self).local_check()
        else:
            self.add_warning(_("%s URL ignored.") % self.scheme.capitalize())
