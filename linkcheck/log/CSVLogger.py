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

import time, linkcheck, linkcheck.Config
from linkcheck.log import strtime
from StandardLogger import StandardLogger

class CSVLogger (StandardLogger):
    """ CSV output. CSV consists of one line per entry. Entries are
    separated by a semicolon.
    """
    def __init__ (self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.separator = args['separator']

    def init (self):
        if self.fd is None: return
        self.starttime = time.time()
        if self.logfield("intro"):
            self.fd.write("# "+(linkcheck._("created by %s at %s\n") % (linkcheck.Config.AppName,
                      strtime(self.starttime))))
            self.fd.write("# "+(linkcheck._("Get the newest version at %s\n") % linkcheck.Config.Url))
            self.fd.write("# "+(linkcheck._("Write comments and bugs to %s\n\n") % \
	                    linkcheck.Config.Email))
            self.fd.write(linkcheck._("# Format of the entries:\n")+\
                          "# urlname;\n"
                          "# recursionlevel;\n"
                          "# parentname;\n"
                      "# baseref;\n"
                      "# errorstring;\n"
                      "# validstring;\n"
                      "# warningstring;\n"
                      "# infostring;\n"
                      "# valid;\n"
                      "# url;\n"
                      "# line;\n"
                      "# name;\n"
                      "# downloadtime;\n"
                      "# checktime;\n"
                      "# cached;\n")
            self.fd.flush()

    def newUrl (self, urlData):
        if self.fd is None: return
        self.fd.write(
	    "%s%s%d%s%s%s%s%s%s%s%s%s%s%s%s%s%d%s%s%s%d%s%s%s%d%s%d%s%d\n" % (
	    urlData.urlName, self.separator,
	    urlData.recursionLevel, self.separator,
	    urlData.parentName, self.separator,
            urlData.baseRef, self.separator,
            urlData.errorString, self.separator,
            urlData.validString, self.separator,
            urlData.warningString, self.separator,
            urlData.infoString, self.separator,
            urlData.valid, self.separator,
            urlData.url, self.separator,
            urlData.line, self.separator,
            urlData.name, self.separator,
            urlData.downloadtime, self.separator,
            urlData.checktime, self.separator,
            urlData.cached))
        self.fd.flush()

    def endOfOutput (self, linknumber=-1):
        if self.fd is None: return
        self.stoptime = time.time()
        if self.logfield("outro"):
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write("# "+linkcheck._("Stopped checking at %s") % strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write(" (%.3f %s)\n" % (duration, name))
            self.fd.flush()
        self.fd = None

