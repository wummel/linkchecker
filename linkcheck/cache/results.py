# -*- coding: iso-8859-1 -*-
# Copyright (C) 2014 Bastian Kleineidam
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
Cache check results.
"""
from ..decorators import synchronized
from ..lock import get_lock


# lock object
cache_lock = get_lock("results_cache_lock")


class ResultCache(object):
    """
    Thread-safe cache of UrlData.to_wire() results.
    the cache is limited in size since we rather recheck the same URL
    multiple times instead of running out of memory.
    format: {cache key (string) -> result (UrlData.towire())}
    """

    def __init__(self, max_size=100000):
        """Initialize result cache."""
        # mapping {URL -> cached result}
        self.cache = {}
        self.max_size = max_size

    @synchronized(cache_lock)
    def get_result(self, key):
        """Return cached result or None if not found."""
        return self.cache.get(key)

    @synchronized(cache_lock)
    def add_result(self, key, result):
        """Add result object to cache with given key.
        The request is ignored when the cache is already full or the key
        is None.
        """
        if len(self.cache) > self.max_size:
            return
        if key is not None:
            self.cache[key] = result

    def has_result(self, key):
        """Non-thread-safe function for fast containment checks."""
        return key in self.cache

    def __len__(self):
        """Get number of cached elements. This is not thread-safe and is
        likely to change before the returned value is used."""
        return len(self.cache)
