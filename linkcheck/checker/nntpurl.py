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

class NoNetrcNNTP (nntplib.NNTP):
    """
    NNTP class ignoring possible entries in ~/.netrc.
    """

    def __init__ (self, host, port=nntplib.NNTP_PORT, user=None,
                  password=None, readermode=None):
        """
        Initialize an instance.  Arguments:
        - host: hostname to connect to
        - port: port to connect to (default the standard NNTP port)
        - user: username to authenticate with
        - password: password to use with username
        - readermode: if true, send 'mode reader' command after
                      connecting.

        readermode is sometimes necessary if you are connecting to an
        NNTP server on the local machine and intend to call
        reader-specific comamnds, such as `group'.  If you get
        unexpected NNTPPermanentErrors, you might need to set
        readermode.
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.file = self.sock.makefile('rb')
        self.debugging = 0
        self.welcome = self.getresp()

        # 'mode reader' is sometimes necessary to enable 'reader' mode.
        # However, the order in which 'mode reader' and 'authinfo' need to
        # arrive differs between some NNTP servers. Try to send
        # 'mode reader', and if it fails with an authorization failed
        # error, try again after sending authinfo.
        readermode_afterauth = 0
        if readermode:
            try:
                self.welcome = self.shortcmd('mode reader')
            except nntplib.NNTPPermanentError:
                # error 500, probably 'not implemented'
                pass
            except nntplib.NNTPTemporaryError, e:
                if user and e.response[:3] == '480':
                    # Need authorization before 'mode reader'
                    readermode_afterauth = 1
                else:
                    raise
        # Perform NNRP authentication if needed.
        if user:
            resp = self.shortcmd('authinfo user '+user)
            if resp[:3] == '381':
                if not password:
                    raise nntplib.NNTPReplyError(resp)
                else:
                    resp = self.shortcmd(
                            'authinfo pass '+password)
                    if resp[:3] != '281':
                        raise nntplib.NNTPPermanentError(resp)
            if readermode_afterauth:
                try:
                    self.welcome = self.shortcmd('mode reader')
                except nntplib.NNTPPermanentError:
                    # error 500, probably 'not implemented'
                    pass


class NntpUrl (urlbase.UrlBase):
    """
    Url link with NNTP scheme.
    """

    def check_connection (self):
        nntpserver = self.host or self.consumer.config["nntpserver"]
        if not nntpserver:
            self.add_warning(
                    _("No NNTP server was specified, skipping this URL."))
            return
        nntp = self._connectNntp(nntpserver)
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

    def _connectNntp (self, nntpserver):
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
                nntp = NoNetrcNNTP(nntpserver)
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
        return False
