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

from Logger import Logger

class BlacklistLogger (Logger):
    """Updates a blacklist of wrong links. If a link on the blacklist
    is working (again), it is removed from the list. So after n days
    we have only links on the list which failed for n days.
    """
    def __init__ (self, **args):
        apply(Logger.__init__, (self,), args)
        self.errors = 0
        self.blacklist = {}
        self.filename = args['filename']

    def init (self):
        pass

    def newUrl (self, urlData):
        if urlData.valid:
            self.blacklist[urlData.getCacheKey()] = None
        elif not urlData.cached:
            self.errors = 1
            self.blacklist[urlData.getCacheKey()] = urlData

    def endOfOutput (self, linknumber=-1):
        """write the blacklist"""
        fd = open(self.filename, "w")
        for url in self.blacklist.keys():
            if self.blacklist[url] is None:
                fd.write(url+"\n")

