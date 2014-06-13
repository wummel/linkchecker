# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2014 Bastian Kleineidam
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
"""
Intern URL pattern support.
"""
import re
from . import urlbase, absolute_url
from .. import strformat, url as urlutil


def get_intern_pattern (url):
    """Return intern pattern for given URL. Redirections to the same
    domain with or without "www." prepended are allowed."""
    parts = strformat.url_unicode_split(url)
    scheme = parts[0].lower()
    domain = parts[1].lower()
    domain, is_idn = urlutil.idna_encode(domain)
    # allow redirection www.example.com -> example.com and vice versa
    if domain.startswith('www.'):
        domain = domain[4:]
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
    args[1] = r"(www\.|)%s" % args[1]
    return "^%s://%s%s" % tuple(args)


class InternPatternUrl (urlbase.UrlBase):
    """Class supporting an intern URL pattern."""

    def get_intern_pattern (self, url=None):
        """
        Get pattern for intern URL matching.

        @return non-empty regex pattern or None
        @rtype String or None
        """
        if url is None:
            url = absolute_url(self.base_url, self.base_ref, self.parent_url)
        if not url:
            return None
        return get_intern_pattern(url)
