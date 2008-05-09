# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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
A blacklist logger.
"""

from __future__ import with_statement
import os
from . import Logger


class BlacklistLogger (Logger):
    """
    Updates a blacklist of wrong links. If a link on the blacklist
    is working (again), it is removed from the list. So after n days
    we have only links on the list which failed for n days.
    """

    def __init__ (self, **args):
        """
        Intialize with old blacklist data (if found, else not).
        """
        super(BlacklistLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.blacklist = {}
        if self.filename is not None and os.path.exists(self.filename):
            self.read_blacklist()

    def comment (self, s, **args):
        """
        Write nothing.
        """
        pass

    def log_url (self, url_data):
        """
        Put invalid url in blacklist, delete valid url from blacklist.
        """
        if not url_data.cached:
            key = url_data.cache_url_key
            if key in self.blacklist:
                if url_data.valid:
                    del self.blacklist[key]
                else:
                    self.blacklist[key] += 1
            else:
                if not url_data.valid:
                    self.blacklist[key] = 1

    def end_output (self):
        """
        Write blacklist file.
        """
        self.write_blacklist()

    def read_blacklist (self):
        """
        Read a previously stored blacklist from file fd.
        """
        with open(self.filename) as fd:
            for line in fd:
                line = self.decode(line.rstrip())
                if line.startswith('#') or not line:
                    continue
                value, key = line.split(None, 1)
                self.blacklist[key] = int(value)

    def write_blacklist (self):
        """
        Write the blacklist.
        """
        oldmask = os.umask(0077)
        for key, value in self.blacklist.items():
            self.write(u"%d %s%s" % (value, key, os.linesep))
        self.close_fileoutput()
        # restore umask
        os.umask(oldmask)
