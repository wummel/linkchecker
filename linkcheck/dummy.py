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
Dummy objects.
"""

class Dummy (object):
    """
    A dummy object ignores all access to it. Useful for testing.
    """

    def __init__ (self, *args, **kwargs):
        pass

    def __call__ (self, *args, **kwargs):
        return self

    def __getattr__ (self, name):
        return self

    def __setattr__ (self, name, value):
        pass

    def __delattr__ (self, name):
        pass

    def __str__ (self):
        return "dummy"

    def __repr__ (self):
        return "<dummy>"

    def __unicode__ (self):
        return u"dummy"

    def __len__ (self):
        return 0

    def __getitem__ (self, key):
        return self

    def __setitem__ (self, key, value):
        pass

    def __delitem__ (self, key):
        pass

    def __contains__ (self, key):
        return False


def dummy (*args, **kwargs):
    """
    Ignore any positional or keyword arguments, return None.
    """
    pass
