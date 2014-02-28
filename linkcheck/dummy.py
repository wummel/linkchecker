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
Dummy objects.
"""

class Dummy (object):
    """A dummy object ignores all access to it. Useful for testing."""

    def __init__ (self, *args, **kwargs):
        """Return None"""
        pass

    def __call__ (self, *args, **kwargs):
        """Return self."""
        return self

    def __getattr__ (self, name):
        """Return self."""
        return self

    def __setattr__ (self, name, value):
        """Return None"""
        pass

    def __delattr__ (self, name):
        """Return None"""
        pass

    def __str__ (self):
        """Return 'dummy'"""
        return "dummy"

    def __repr__ (self):
        """Return '<dummy>'"""
        return "<dummy>"

    def __unicode__ (self):
        """Return u'dummy'"""
        return u"dummy"

    def __len__ (self):
        """Return zero"""
        return 0

    def __getitem__ (self, key):
        """Return self"""
        return self

    def __setitem__ (self, key, value):
        """Return None"""
        pass

    def __delitem__ (self, key):
        """Return None"""
        pass

    def __contains__ (self, key):
        """Return False"""
        return False


def dummy (*args, **kwargs):
    """Ignore any positional or keyword arguments, return None."""
    pass
