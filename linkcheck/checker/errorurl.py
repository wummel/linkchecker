# -*- coding: iso-8859-1 -*-
# Copyright (C) 2001-2005  Bastian Kleineidam
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
Handle for unknown links.
"""

import urlbase
import linkcheck

class ErrorUrl (urlbase.UrlBase):
    """
    Unknown URL links.
    """

    def check_syntax (self):
        """
        Log a warning that the URL syntax is invalid or unknown.
        """
        assert linkcheck.log.debug(linkcheck.LOG_CHECK, "checking syntax")
        self.url, is_idn = linkcheck.url.url_norm(self.base_url)
        self.set_result(_("URL is unrecognized or has invalid syntax"),
                        valid=False)
        return False

    def set_cache_keys (self):
        """
        Cache key is forbidden.
        """
        raise NotImplementedError, "cache keys are forbidden"
