# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Handle nntp: and news: links.
"""

import re
import time
import nntplib
import random

from . import urlbase
from .. import log, LinkCheckerError, LOG_CHECK
from .const import WARN_NNTP_NO_SERVER, WARN_NNTP_NO_NEWSGROUP

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
        nntpserver = self.host or self.aggregate.config["nntpserver"]
        if not nntpserver:
            self.add_warning(
                    _("No NNTP server was specified, skipping this URL."),
                    tag=WARN_NNTP_NO_SERVER)
            return
        nntp = self._connect_nntp(nntpserver)
        group = self.urlparts[2]
        while group[:1] == '/':
            group = group[1:]
        if '@' in group:
            # request article info (resp, number mid)
            number = nntp.stat("<"+group+">")[1]
            self.add_info(_('Article number %(num)s found.') % {"num": number})
        else:
            # split off trailing articel span
            group = group.split('/', 1)[0]
            if group:
                # request group info (resp, count, first, last, name)
                name = nntp.group(group)[4]
                self.add_info(_("News group %(name)s found.") % {"name": name})
            else:
                # group name is the empty string
                self.add_warning(_("No newsgroup specified in NNTP URL."),
                            tag=WARN_NNTP_NO_NEWSGROUP)

    def _connect_nntp (self, nntpserver):
        """
        This is done only once per checking task. Also, the newly
        introduced error codes 504 and 505 (both inclining "Too busy, retry
        later", are caught.
        """
        tries = 0
        nntp = None
        while tries < 2:
            tries += 1
            try:
                nntp = nntplib.NNTP(nntpserver, usenetrc=False)
            except nntplib.NNTPTemporaryError:
                self.wait()
            except nntplib.NNTPPermanentError as msg:
                if re.compile("^50[45]").search(str(msg)):
                    self.wait()
                else:
                    raise
        if nntp is None:
            raise LinkCheckerError(
               _("NNTP server too busy; tried more than %d times.") % tries)
        if log.is_debug(LOG_CHECK):
            nntp.set_debuglevel(1)
        self.add_info(nntp.getwelcome())
        return nntp

    def wait (self):
        """Wait some time before trying to connect again."""
        time.sleep(random.randrange(10, 30))

    def can_get_content (self):
        """
        NNTP urls have no content.

        @return: False
        @rtype: bool
        """
        return False
