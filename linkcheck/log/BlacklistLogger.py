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

import os
from Logger import Logger
from linkcheck.Config import norm

class BlacklistLogger (Logger):
    """Updates a blacklist of wrong links. If a link on the blacklist
    is working (again), it is removed from the list. So after n days
    we have only links on the list which failed for n days.
    """
    def __init__ (self, **args):
        super(BlacklistLogger, self).__init__(**args)
        self.errors = 0
        self.blacklist = {}
        self.filename = norm(args['filename'])
        if os.path.exists(self.filename):
            self.readBlacklist()


    def newUrl (self, urlData):
        if not urlData.cached:
            key = urlData.getCacheKey()
            if key in self.blacklist:
                if urlData.valid:
                    del self.blacklist[key]
                else:
                    self.blacklist[key] += 1
            else:
                if not urlData.valid:
                    self.blacklist[key] = 1


    def endOfOutput (self, linknumber=-1):
        self.writeBlacklist()


    def readBlacklist (self):
        fd = file(self.filename, "r")
        for line in fd:
            value, key = line.split(1)
            self.blacklist[key] = int(value)
        fd.close()


    def writeBlacklist (self):
        """write the blacklist"""
        fd = file(self.filename, "w")
        for key, value in self.blacklist.items():
            fd.write("%d %s\n" % (value, key))
        fd.close()
