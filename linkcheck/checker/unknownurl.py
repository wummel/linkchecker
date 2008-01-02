# -*- coding: iso-8859-1 -*-
# Copyright (C) 2001-2008 Bastian Kleineidam
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
Handle uncheckable URLs.
"""

import re
import urlbase
from const import WARN_IGNORE_URL

ignored_schemes = r"""^(
acap        # application configuration access protocol
|afs        # Andrew File System global file names
|cid        # content identifier
|data       # data
|dav        # dav
|fax        # fax
|imap       # internet message access protocol
|ldap       # Lightweight Directory Access Protocol
|mailserver # Access to data available from mail servers
|mid        # message identifier
|mms        # multimedia stream
|modem      # modem
|nfs        # network file system protocol
|opaquelocktoken # opaquelocktoken
|pop        # Post Office Protocol v3
|prospero   # Prospero Directory Service
|rsync      # rsync protocol
|rtsp       # real time streaming protocol
|rtspu      # real time streaming protocol
|service    # service location
|shttp      # secure HTTP
|sip        # session initiation protocol
|tel        # telephone
|tip        # Transaction Internet Protocol
|tn3270     # Interactive 3270 emulation sessions
|vemmi      # versatile multimedia interface
|wais       # Wide Area Information Servers
|z39\.50r   # Z39.50 Retrieval
|z39\.50s   # Z39.50 Session
|chrome     # Mozilla specific
|find       # Mozilla specific
|clsid      # Microsoft specific
|javascript # JavaScript
|isbn       # ISBN (int. book numbers)
):"""

ignored_schemes_re = re.compile(ignored_schemes, re.VERBOSE)

is_unknown_url = ignored_schemes_re.search


class UnknownUrl (urlbase.UrlBase):
    """
    Handle unknown or just plain broken URLs.
    """

    def local_check (self):
        """
        Only logs that this URL is unknown.
        """
        self.set_extern(self.url)
        if self.extern[0] and self.extern[1]:
            self.add_info(_("Outside of domain filter, checked only syntax."))
        elif self.ignored():
            self.add_warning(_("%s URL ignored.") % self.scheme.capitalize(),
                             tag=WARN_IGNORE_URL)
        else:
            self.set_result(_("URL is unrecognized or has invalid syntax"),
                        valid=False)

    def ignored (self):
        return ignored_schemes_re.search(self.url)

    def can_get_content (self):
        """
        Unknown URLs have no content.

        @return: False
        @rtype: bool
        """
        return False
