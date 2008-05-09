# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2008 Bastian Kleineidam
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
from . import urlbase, absolute_url
from .. import strformat, url as urlutil

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
        url = absolute_url(self.base_url, self.base_ref, self.parent_url)
        if not url:
            return None
        parts = strformat.url_unicode_split(url)
        scheme = parts[0]
        domain = parts[1]
        domain, is_idn = urlutil.idna_encode(domain)
        if is_idn:
            pass # XXX warn about idn use
        if not (domain and scheme):
            return None
        path = urlutil.splitparams(parts[2])[0]
        segments = path.split('/')[:-1]
        path = "/".join(segments)
        if url.endswith('/'):
            path += '/'
        args = list(re.escape(x) for x in (scheme, domain, path))
        if args[0] in ('http', 'https'):
            args[0] = 'https?'
        if args[1].startswith('www\\.'):
            args[1] = r"(www\.|)%s" % args[1][5:]
        return "%s://%s%s" % tuple(args)
