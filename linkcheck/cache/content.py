# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012 Bastian Kleineidam
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
Cache for content checksums.
"""
import hashlib
from ..lock import get_lock
from ..decorators import synchronized

_lock = get_lock("checksums")

class ChecksumInfo(object):
    """Cache for content checksums."""

    def __init__(self):
        """Initialize checksums and cache statistics."""
        # {hash -> [URL]}
        self.checksums = {}
        self.misses = self.hits = 0

    def get_checksum_urls(self, url, checksum):
        """Look for and store checksum for URL.
        @param url: the URL for the checksum
        @ptype url: unicode
        @param checksum: the URL content checksum
        @ptype checksum: str
        @return: list of URLs matching the given checksum (except the given URL)
        @rtype: list of unicode
        """
        if checksum in self.checksums:
            self.hits += 1
            urls = self.checksums[checksum]
            if url in urls:
                res = [x for x in urls if x != url]
            else:
                res = urls[:]
                urls.append(url)
        else:
            self.misses += 1
            res = []
            self.checksums[checksum] = [url]
        return res


_checksuminfo = ChecksumInfo()

@synchronized(_lock)
def get_checksum_urls(url, content):
    """See if given URL content is already stored under another URL.
    @param url: the URL for which the content is valid
    @ptype url: unicode
    @param content: the content to hash
    @ptype content: str
    @return: list of URLs with the same content (except the given URL)
    @rtype: list of unicode"""
    checksum = hashlib.sha1(content).hexdigest()
    return _checksuminfo.get_checksum_urls(url, checksum)
