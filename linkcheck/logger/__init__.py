# -*- coding: iso-8859-1 -*-
"""Output logging support for different formats"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

# dummy translator
_ = lambda x: x

# known field names, translated
Fields = {
    "realurl":   _("Real URL"),
    "cachekey":  _("Cache key"),
    "result":    _("Result"),
    "base":      _("Base"),
    "name":      _("Name"),
    "parenturl": _("Parent URL"),
    "extern":    _("Extern"),
    "info":      _("Info"),
    "warning":   _("Warning"),
    "dltime":    _("D/L Time"),
    "dlsize":    _("D/L Size"),
    "checktime": _("Check Time"),
    "url":       _("URL"),
}

# real translator
from linkcheck.i18n import _


class Logger (object):
    """basic logger class enabling logging of checked urls"""

    def __init__ (self, **kwargs):
        """initialize a logger, looking for field restrictions in kwargs"""
        self.logfields = None # log all fields
        self.logspaces = {}
        self.max_indent = 0
        if kwargs.has_key('fields'):
            if "all" not in kwargs['fields']:
                # only log given fields
                self.logfields = kwargs['fields']

    def has_field (self, name):
        """see if given field name will be logged"""
        if self.logfields is None:
            # log all fields
            return True
        return name in self.logfields

    def field (self, name):
        """return translated field name"""
        return _(Fields[name])

    def spaces (self, name):
        """return indent of spaces for given field name"""
        return self.logspaces[name]

    def start_output (self):
        """start log output"""
        # map with spaces between field name and value
        if self.logfields is None:
            fields = Fields.keys()
        else:
            fields = self.logfields
        values = [self.field(x) for x in fields]
        # maximum indent for localized log field names
        self.max_indent = max(map(lambda x: len(x), values))+1
        for key in fields:
            self.logspaces[key] = " "*(self.max_indent - len(self.field(key)))

    def new_url (self, url_data):
        """log a new url with this logger"""
        raise NotImplementedError, "abstract function"

    def end_output (self, linknumber=-1):
        """end of output, used for cleanup (eg output buffer flushing)"""
        raise NotImplementedError, "abstract function"

    def __str__ (self):
        """return class name"""
        return self.__class__.__name__

    def __repr__ (self):
        """return class name"""
        return repr(self.__class__.__name__)

