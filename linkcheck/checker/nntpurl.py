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
Handle nntp: and news: links.
"""

import re
import time
import sys
import nntplib
import socket
import urlparse
import random

import linkcheck
import urlbase
import linkcheck.log

random.seed()

class NntpUrl (urlbase.UrlBase):
    """
    Url link with NNTP scheme.
    """

    def check_connection (self):
        """
        Connect to NNTP server and try to request the URL article
        resource (if specified).
        """
        nntpserver = self.host or self.consumer.config["nntpserver"]
        if not nntpserver:
            self.add_warning(
                    _("No NNTP server was specified, skipping this URL."))
            return
        nntp = self._connect_nntp(nntpserver)
        group = self.urlparts[2]
        while group[:1] == '/':
            group = group[1:]
        if '@' in group:
            # request article
            resp, number, mid = nntp.stat("<"+group+">")
            self.add_info(_('Articel number %s found.') % number)
        else:
            # split off trailing articel span
            group = group.split('/', 1)[0]
            if group:
                # request group info
                resp, count, first, last, name = nntp.group(group)
                self.add_info(_("Group %s has %s articles, range %s to %s.")%\
                             (name, count, first, last))
            else:
                # group name is the empty string
                self.add_warning(_("No newsgroup specified in NNTP URL."))

    def _connect_nntp (self, nntpserver):
        """
        This is done only once per checking task. Also, the newly
        introduced error codes 504 and 505 (both inclining "Too busy, retry
        later", are caught.
        """
        tries = 0
        nntp = value = None
        while tries < 5:
            tries += 1
            try:
                nntp = nntplib.NNTP(nntpserver, usenetrc=False)
            except nntplib.error_perm:
                value = sys.exc_info()[1]
                if re.compile("^50[45]").search(str(value)):
                    time.sleep(random.randrange(10, 30))
                else:
                    raise
        if nntp is None:
            raise linkcheck.LinkCheckerError(
               _("NTTP server too busy; tried more than %d times.") % tries)
        if value is not None:
            self.add_warning(_("NNTP busy: %s.") % str(value))
        return nntp

    def can_get_content (self):
        """
        NNTP urls have no content.

        @return: False
        @rtype: bool
        """
        return False
