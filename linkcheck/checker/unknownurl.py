# -*- coding: iso-8859-1 -*-
# Copyright (C) 2001-2014 Bastian Kleineidam
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


class UnknownUrl (urlbase.UrlBase):
    """Handle unknown or just plain broken URLs."""

    def build_url (self):
        """Only logs that this URL is unknown."""
        super(UnknownUrl, self).build_url()
        if self.is_ignored():
            self.add_info(_("%(scheme)s URL ignored.") %
                          {"scheme": self.scheme.capitalize()})
            self.set_result(_("ignored"))
        else:
            self.set_result(_("URL is unrecognized or has invalid syntax"),
                        valid=False)

    def is_ignored (self):
        """Return True if this URL scheme is ignored."""
        return is_unknown_scheme(self.scheme)

    def can_get_content (self):
        """Unknown URLs have no content.

        @return: False
        @rtype: bool
        """
        return False


# do not edit anything below since these entries are generated from
# scripts/update_iana_uri_schemes.sh
# DO NOT REMOVE

# from https://www.iana.org/assignments/uri-schemes/uri-schemes.xhtml
ignored_schemes_permanent = r"""
|aaa        # Diameter Protocol
|aaas       # Diameter Protocol with Secure Transport
|about      # about
|acap       # application configuration access protocol
|acct       # acct
|cap        # Calendar Access Protocol
|cid        # content identifier
|coap       # coap
|coaps      # coaps
|crid       # TV-Anytime Content Reference Identifier
|data       # data
|dav        # dav
|dict       # dictionary service protocol
|dns        # Domain Name System
|geo        # Geographic Locations
|go         # go
|gopher     # The Gopher Protocol
|h323       # H.323
|iax        # Inter-Asterisk eXchange Version 2
|icap       # Internet Content Adaptation Protocol
|im         # Instant Messaging
|imap       # internet message access protocol
|info       # Information Assets with Identifiers in Public Namespaces
|ipp        # Internet Printing Protocol
|iris       # Internet Registry Information Service
|iris\.beep # iris.beep
|iris\.lwz  # iris.lwz
|iris\.xpc  # iris.xpc
|iris\.xpcs # iris.xpcs
|jabber     # jabber
|ldap       # Lightweight Directory Access Protocol
|mid        # message identifier
|msrp       # Message Session Relay Protocol
|msrps      # Message Session Relay Protocol Secure
|mtqp       # Message Tracking Query Protocol
|mupdate    # Mailbox Update (MUPDATE) Protocol
|nfs        # network file system protocol
|ni         # ni
|nih        # nih
|opaquelocktoken # opaquelocktokent
|pop        # Post Office Protocol v3
|pres       # Presence
|reload     # reload
|rtsp       # Real-time Streaming Protocol (RTSP)
|rtsps      # Real-time Streaming Protocol (RTSP) over TLS
|rtspu      # Real-time Streaming Protocol (RTSP) over unreliable datagram transport
|service    # service location
|session    # session
|shttp      # Secure Hypertext Transfer Protocol
|sieve      # ManageSieve Protocol
|sip        # session initiation protocol
|sips       # secure session initiation protocol
|sms        # Short Message Service
|snmp       # Simple Network Management Protocol
|soap\.beep # soap.beep
|soap\.beeps # soap.beeps
|stun       # stun
|stuns      # stuns
|tag        # tag
|tel        # telephone
|telnet     # Reference to interactive sessions
|tftp       # Trivial File Transfer Protocol
|thismessage # multipart/related relative reference resolution
|tip        # Transaction Internet Protocol
|tn3270     # Interactive 3270 emulation sessions
|turn       # turn
|turns      # turns
|tv         # TV Broadcasts
|urn        # Uniform Resource Names
|vemmi      # versatile multimedia interface
|ws         # WebSocket connections
|wss        # Encrypted WebSocket connections
|xcon       # xcon
|xcon\-userid # xcon-userid
|xmlrpc\.beep # xmlrpc.beep
|xmlrpc\.beeps # xmlrpc.beeps
|xmpp       # Extensible Messaging and Presence Protocol
|z39\.50r   # Z39.50 Retrieval
|z39\.50s   # Z39.50 Session
"""

ignored_schemes_provisional = r"""
|adiumxtra  # adiumxtra
|afp        # afp
|afs        # Andrew File System global file names
|aim        # aim
|apt        # apt
|attachment # attachment
|aw         # aw
|barion     # barion
|beshare    # beshare
|bitcoin    # bitcoin
|bolo       # bolo
|callto     # callto
|chrome     # chrome
|chrome\-extension # chrome-extension
|com\-eventbrite\-attendee # com-eventbrite-attendee
|content    # content
|cvs        # cvs
|dlna\-playcontainer # dlna-playcontainer
|dlna\-playsingle # dlna-playsingle
|dtn        # DTNRG research and development
|dvb        # dvb
|ed2k       # ed2k
|facetime   # facetime
|feed       # feed
|feedready  # feedready
|finger     # finger
|fish       # fish
|gg         # gg
|git        # git
|gizmoproject # gizmoproject
|gtalk      # gtalk
|ham        # ham
|hcp        # hcp
|icon       # icon
|ipn        # ipn
|irc        # irc
|irc6       # irc6
|ircs       # ircs
|itms       # itms
|jar        # jar
|jms        # Java Message Service
|keyparc    # keyparc
|lastfm     # lastfm
|ldaps      # ldaps
|magnet     # magnet
|maps       # maps
|market     # market
|message    # message
|mms        # mms
|ms\-help   # ms-help
|ms\-settings\-power # ms-settings-power
|msnim      # msnim
|mumble     # mumble
|mvn        # mvn
|notes      # notes
|oid        # oid
|palm       # palm
|paparazzi  # paparazzi
|pkcs11     # pkcs11
|platform   # platform
|proxy      # proxy
|psyc       # psyc
|query      # query
|res        # res
|resource   # resource
|rmi        # rmi
|rsync      # rsync
|rtmp       # rtmp
|secondlife # query
|sftp       # query
|sgn        # sgn
|skype      # skype
|smb        # smb
|smtp       # smtp
|soldat     # soldat
|spotify    # spotify
|ssh        # ssh
|steam      # steam
|submit     # submit
|svn        # svn
|teamspeak  # teamspeak
|things     # things
|udp        # udp
|unreal     # unreal
|ut2004     # ut2004
|ventrilo   # ventrilo
|view\-source # view-source
|webcal     # webcal
|wtai       # wtai
|wyciwyg    # wyciwyg
|xfire      # xfire
|xri        # xri
|ymsgr      # ymsgr
"""

ignored_schemes_historical = r"""
|fax        # fax
|mailserver # Access to data available from mail servers
|modem      # modem
|pack       # pack
|prospero   # Prospero Directory Service
|snews      # NNTP over SSL/TLS
|videotex   # videotex
|wais       # Wide Area Information Servers
|z39\.50    # Z39.50 information access
"""

ignored_schemes_other = r"""
|clsid      # Microsoft specific
|find       # Mozilla specific
|isbn       # ISBN (int. book numbers)
|javascript # JavaScript
"""

ignored_schemes = "^(%s%s%s%s)$" % (
    ignored_schemes_permanent,
    ignored_schemes_provisional,
    ignored_schemes_historical,
    ignored_schemes_other,
)
ignored_schemes_re = re.compile(ignored_schemes, re.VERBOSE)

is_unknown_scheme = ignored_schemes_re.match

