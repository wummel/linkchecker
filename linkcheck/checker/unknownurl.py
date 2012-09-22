# -*- coding: iso-8859-1 -*-
# Copyright (C) 2001-2012 Bastian Kleineidam
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
Handle uncheckable URLs.
"""

import re
from . import urlbase
from .const import WARN_IGNORE_URL

# from http://www.iana.org/assignments/uri-schemes.html
ignored_schemes_permanent = r"""
aaas?       # Diameter Protocol
|about      # about
|acap       # application configuration access protocol
|cap        # Calendar Access Protocol
|cid        # content identifier
|crid       # TV-Anytime Content Reference Identifier
|data       # data
|dav        # dav
|dict       # dictionary service protocol
|dns        # Domain Name System
|geo        # Geographic Locations
|go         # go
|gopher     # Gopher
|h323       # H.323
|iax        # Inter-Asterisk eXchange Version 2
|icap       # Internet Content Adaptation Protocol
|im         # Instant Messaging
|imap       # internet message access protocol
|info       # Information Assets with Identifiers in Public Namespaces
|ipp        # Internet Printing Protocol
|iris       # Internet Registry Information Service
|iris\.(beep|xpcs?|lwz) #
|ldap       # Lightweight Directory Access Protocol
|mid        # message identifier
|msrps?     # Message Session Relay Protocol
|mtqp       # Message Tracking Query Protocol
|mupdate    # Mailbox Update (MUPDATE) Protocol
|nfs        # network file system protocol
|nih?       #
|opaquelocktoken # opaquelocktoken
|pop        # Post Office Protocol v3
|pres       # Presence
|rtsp       # real time streaming protocol
|service    # service location
|session    #
|shttp      # secure HTTP
|sieve      # ManageSieve Protocol
|sips?      # session initiation protocol
|sms        # Short Message Service
|snmp       # Simple Network Management Protocol
|soap\.beeps? #
|steam      # Steam browser protocol
|tag        #
|tel        # telephone
|tftp       # Trivial File Transfer Protocol
|thismessage #
|tip        # Transaction Internet Protocol
|tn3270     # Interactive 3270 emulation sessions
|tv         # TV Broadcasts
|urn        # Uniform Resource Names
|vemmi      # versatile multimedia interface
|wss?       # WebSocket connections
|xcon(-userid)? #
|xmlrpc\.beeps? #
|xmpp       #
|z39\.50r   # Z39.50 Retrieval
|z39\.50s   # Z39.50 Session
"""

ignored_schemes_provisional = r"""
|afs        # Andrew File System global file names
|callto     #
|com-eventbrite-attendee #
|dlna-play(single|container) #
|dtn        # DTNRG research and development
|dvb        #
|hcp        #
|icon       #
|ipn        #
|jms        # Java Message Service
|mms        # multimedia stream
|ms-help    #
|msnim      #
|oid        #
|res        #
|rsync      # rsync protocol
|skype      # Skype
|view-source #
"""

ignored_schemes_historical = r"""
|fax        # fax
|mailserver # Access to data available from mail servers
|modem      # modem
|prospero   # Prospero Directory Service
|videotex   #
|wais       # Wide Area Information Servers
|z39\.50    # Z39.50 information access
"""

ignored_schemes_other = r"""
|chrome     # Mozilla specific
|clsid      # Microsoft specific
|feed       # RSS or Atom feeds
|find       # Mozilla specific
|isbn       # ISBN (int. book numbers)
|ircs?      # internet relay chat
|javascript # JavaScript
"""


ignored_schemes = "^(%s%s%s%s):" % (
    ignored_schemes_permanent,
    ignored_schemes_provisional,
    ignored_schemes_historical,
    ignored_schemes_other,
)
ignored_schemes_re = re.compile(ignored_schemes, re.VERBOSE)

is_unknown_url = ignored_schemes_re.search


class UnknownUrl (urlbase.UrlBase):
    """Handle unknown or just plain broken URLs."""

    def local_check (self):
        """Only logs that this URL is unknown."""
        if self.extern[0] and self.extern[1]:
            self.add_info(_("Outside of domain filter, checked only syntax."))
        elif self.ignored():
            self.add_warning(_("%(scheme)s URL ignored.") %
                             {"scheme": self.scheme.capitalize()},
                             tag=WARN_IGNORE_URL)
        else:
            self.set_result(_("URL is unrecognized or has invalid syntax"),
                        valid=False)

    def ignored (self):
        """Return True if this URL scheme is ignored."""
        return ignored_schemes_re.search(self.url)

    def can_get_content (self):
        """Unknown URLs have no content.

        @return: False
        @rtype: bool
        """
        return False
