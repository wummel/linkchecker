# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2003  Bastian Kleineidam
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

from linkcheck import i18n as i18nreal
class i18ndummy:
    """dummy class to defer translation, but enable pygettext"""
    _ = lambda self, s: s
i18n = i18ndummy()

class Logger (object):
    Fields = {
        "realurl":   i18n._("Real URL"),
        "result":    i18n._("Result"),
        "base":      i18n._("Base"),
        "name":      i18n._("Name"),
        "parenturl": i18n._("Parent URL"),
        "extern":    i18n._("Extern"),
        "info":      i18n._("Info"),
        "warning":   i18n._("Warning"),
        "dltime":    i18n._("D/L Time"),
        "dlsize":    i18n._("D/L Size"),
        "checktime": i18n._("Check Time"),
        "url":       i18n._("URL"),
    }


    def __init__ (self, **args):
        self.logfields = None # log all fields
        if args.has_key('fields'):
            if "all" not in args['fields']:
                self.logfields = args['fields']


    def has_field (self, name):
        if self.logfields is None:
            # log all fields
            return True
        return name in self.logfields


    def field (self, name):
        """return translated field name"""
        return i18nreal._(self.Fields[name])


    def spaces (self, name):
        return self.logspaces[name]


    def init (self):
        # map with spaces between field name and value
        self.logspaces = {}
        if self.logfields is None:
            fields = self.Fields.keys()
        else:
            fields = self.logfields
        values = [self.field(x) for x in fields]
        # maximum indent for localized log field names
        self.max_indent = max(map(lambda x: len(x), values))+1
        for key in fields:
            self.logspaces[key] = " "*(self.max_indent - len(self.field(key)))


    def newUrl (self, urlData):
        raise Exception, "abstract function"


    def endOfOutput (self, linknumber=-1):
        raise Exception, "abstract function"


    def __str__ (self):
        return self.__class__.__name__


    def __repr__ (self):
        return `self.__class__.__name__`
