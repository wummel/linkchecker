# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2005  Bastian Kleineidam
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

import sys
import os

import linkcheck
import linkcheck.logger


class BlacklistLogger (linkcheck.logger.Logger):
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
        self.blacklist = {}
        if args.get('fileoutput'):
            self.fileoutput = True
            filename = args['filename']
            if os.path.exists(filename):
                self.read_blacklist(file(filename, "r"))
            self.fd = file(filename, "w")
        elif args.has_key('fd'):
            self.fd = args['fd']
        else:
            self.fileoutput = False
            self.fd = sys.stdout

    def comment (self, s, **args):
        """
        Print nothing.
        """
        pass

    def new_url (self, url_data):
        """
        Put invalid url in blacklist, delete valid url from blacklist.
        """
        if not url_data.cached:
            key = url_data.getCacheKey()
            if key in self.blacklist:
                if url_data.valid:
                    del self.blacklist[key]
                else:
                    self.blacklist[key] += 1
            else:
                if not url_data.valid:
                    self.blacklist[key] = 1

    def end_output (self, linknumber=-1):
        """
        Write blacklist file.
        """
        self.write_blacklist()

    def read_blacklist (self, fd):
        """
        Read a previously stored blacklist from file fd.
        """
        for line in fd:
            line = line.rstrip()
            if line.startswith('#') or not line:
                continue
            value, key = line.split(None, 1)
            self.blacklist[key] = int(value)
        fd.close()

    def write_blacklist (self):
        """
        Write the blacklist.
        """
        oldmask = os.umask(0077)
        for key, value in self.blacklist.items():
            self.fd.write("%d %s" % (value, key))
            self.fd.write(os.linesep)
        if self.fileoutput:
            self.fd.close()
        # restore umask
        os.umask(oldmask)
