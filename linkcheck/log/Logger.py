# Copyright (C) 2000-2002  Bastian Kleineidam
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

from linkcheck import _

class Logger:
    Fields = {
        "realurl":   lambda: _("Real URL"),
        "result":    lambda: _("Result"),
        "base":      lambda: _("Base"),
        "name":      lambda: _("Name"),
        "parenturl": lambda: _("Parent URL"),
        "extern":    lambda: _("Extern"),
        "info":      lambda: _("Info"),
        "warning":   lambda: _("Warning"),
        "dltime":    lambda: _("D/L Time"),
        "dlsize":    lambda: _("D/L Size"),
        "checktime": lambda: _("Check Time"),
        "url":       lambda: _("URL"),
    }

    def __init__ (self, **args):
        self.logfields = None # log all fields
        if args.has_key('fields'):
            if "all" not in args['fields']:
                self.logfields = args['fields']

    def has_field (self, name):
        if self.logfields is None:
            # log all fields
            return 1
        return name in self.logfields

    def field (self, name):
        return self.Fields[name]()

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
