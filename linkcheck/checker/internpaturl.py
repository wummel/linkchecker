# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2006 Bastian Kleineidam
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
Intern URL pattern support.
"""
import re
import urlbase
import linkcheck.checker

class InternPatternUrl (urlbase.UrlBase):
    """
    Class supporting an intern URL pattern.
    """

    def get_intern_pattern (self):
        """
        Get pattern for intern URL matching.

        @return non-empty regex pattern or None
        @rtype String or None
        """
        absolute = linkcheck.checker.absolute_url
        url = absolute(self.base_url, self.base_ref, self.parent_url)
        if not url:
            return None
        parts = linkcheck.strformat.url_unicode_split(url)
        scheme = parts[0]
        domain = parts[1]
        domain, is_idn = linkcheck.url.idna_encode(domain)
        if not (domain and scheme):
            return None
        path, params = linkcheck.url.splitparams(parts[2])
        segments = path.split('/')[:-1]
        path = "/".join(segments)
        args = tuple(re.escape(x) for x in (scheme, domain, path))
        return "%s://%s%s" % args
