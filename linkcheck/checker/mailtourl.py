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
Handle for mailto: links.
"""

import cgi
import urllib
import smtplib
import email.Utils

import urlbase
from .. import log, LOG_CHECK
import linkcheck.strformat
import linkcheck.dns.resolver
from const import WARN_MAIL_NO_ADDRESSES, WARN_MAIL_NO_MX_HOST, \
    WARN_MAIL_UNVERIFIED_ADDRESS, WARN_MAIL_NO_CONNECTION


def _split_address (address):
    """
    Split username and hostname of address. The hostname defaults
    to 'localhost' if it is not specified.

    @param address: an email address
    @type address: string
    @return: a tuple (username, hostname)
    @rtype: tuple
    @raise: LinkCheckerError if address could not be split
    """
    split = address.split("@", 1)
    if len(split) == 2:
        if not split[1]:
            return (split[0], "localhost")
        return tuple(split)
    if len(split) == 1:
        return (split[0], "localhost")
    raise linkcheck.LinkCheckerError(_("Could not split the mail address"))


class MailtoUrl (urlbase.UrlBase):
    """
    Url link with mailto scheme.
    """

    def build_url (self):
        """
        Call super.build_url(), extract list of mail addresses from URL,
        and check their syntax.
        """
        super(MailtoUrl, self).build_url()
        self.headers = {}
        self.addresses = email.Utils.getaddresses([self.cutout_addresses()])
        for key in ("to", "cc", "bcc"):
            if key in self.headers:
                for val in self.headers[key]:
                    a = urllib.unquote(val)
                    self.addresses.extend(email.Utils.getaddresses([a]))
        # check syntax of emails
        for name, addr in self.addresses:
            username, domain = _split_address(addr)
            if not linkcheck.url.is_safe_domain(domain):
                raise linkcheck.LinkCheckerError(_("Invalid mail syntax"))
        log.debug(LOG_CHECK, "addresses: %s", self.addresses)

    def cutout_addresses (self):
        """
        Parse all mail addresses out of the URL target. Additionally
        store headers.

        @return: comma separated list of email addresses
        @rtype: string
        """
        # cut off leading mailto: and unquote
        url = urllib.unquote(self.base_url[7:])
        # search for cc, bcc, to and store in headers
        mode = 0 # 0=default, 1=quote, 2=esc
        quote = None
        i = 0
        for i, c in enumerate(url):
            if mode == 0:
                if c == '?':
                    break
                elif c in '<"':
                    quote = c
                    mode = 1
                elif c == '\\':
                    mode = 2
            elif mode==1:
                if c == '"' and quote == '"':
                    mode = 0
                elif c == '>' and quote == '<':
                    mode = 0
            elif mode == 2:
                mode = 0
        if i < (len(url) - 1):
            try:
                headers = cgi.parse_qs(url[(i+1):], strict_parsing=True)
                for key, val in headers.items():
                    self.headers.setdefault(key.lower(), []).extend(val)
            except ValueError, err:
                self.add_warning(_("Error parsing CGI values: %s") % str(err))
            addrs = url[:i]
        else:
            addrs = url
        # addrs is comma-separated list of mails now
        return addrs

    def check_connection (self):
        """
        Verify a list of email addresses. If one address fails,
        the whole list will fail.

        For each mail address we check the following things:
          1. Look up the MX DNS records. If we found no MX record,
             print an error.
          2. Check if one of the mail hosts accept an SMTP connection.
             Check hosts with higher priority first.
             If no host accepts SMTP, we print a warning.
          3. Try to verify the address with the VRFY command. If we got
             an answer, print the verified address as an info.
             If not, print a warning.
        """
        if not self.addresses:
            self.add_warning(_("No addresses found."),
                             tag=WARN_MAIL_NO_ADDRESSES)
            return
        for name, mail in self.addresses:
            self.check_smtp_domain(name, mail)


    def check_smtp_domain (self, name, mail):
        """
        Check a single mail address.
        """
        log.debug(LOG_CHECK, "checking mail address %r", mail)
        mail = linkcheck.strformat.ascii_safe(mail)
        username, domain = _split_address(mail)
        log.debug(LOG_CHECK, "looking up MX mailhost %r", domain)
        try:
            answers = linkcheck.dns.resolver.query(domain, 'MX')
        except linkcheck.dns.resolver.NoAnswer:
            answers = []
        if len(answers) == 0:
            self.add_warning(_("No MX mail host for %(domain)s found.") %
                            {'domain': domain},
                             tag=WARN_MAIL_NO_MX_HOST)
            answers = linkcheck.dns.resolver.query(domain, 'A')
            if len(answers) == 0:
                self.set_result(_("No host for %(domain)s found.") %
                                 {'domain': domain}, valid=False)
                return
            # set preference to zero
            mxdata = [(0, rdata.to_text(omit_final_dot=True))
                      for rdata in answers]
        else:
            mxdata = [(rdata.preference,
                       rdata.exchange.to_text(omit_final_dot=True))
                       for rdata in answers]
            # sort according to preference (lower preference means this
            # host should be preferred)
            mxdata.sort()
        # debug output
        log.debug(LOG_CHECK, "found %d MX mailhosts:", len(answers))
        for preference, host in mxdata:
            log.debug(LOG_CHECK,
                "MX host %r, preference %d", host, preference)
        # connect
        self.check_smtp_connect(mxdata, username, domain)

    def check_smtp_connect (self, mxdata, username, domain):
        """
        Connect to SMTP servers and check emails.

        @param mxdata: list of (preference, host) tuples to check for
        @type mxdata: list
        @param username: the username to verify
        @type username: string
        """
        smtpconnect = 0
        for preference, host in mxdata:
            try:
                log.debug(LOG_CHECK,
                    "SMTP check for %r (preference %d)", host, preference)
                self.url_connection = smtplib.SMTP()
                if log.is_debug(LOG_CHECK):
                    self.url_connection.set_debuglevel(1)
                self.url_connection.connect(host)
                log.debug(LOG_CHECK, "SMTP connected!")
                smtpconnect = 1
                self.url_connection.helo()
                info = self.url_connection.verify("%s@%s" % (username, domain))
                log.debug(LOG_CHECK, "SMTP user info %r", info)
                d = {'info': str(info[1])}
                if info[0] == 250:
                    self.add_info(_("Verified address: %(info)s.") % d)
                # check for 25x return code which means that the address
                # could not be verified, but is sent anyway
                elif 0 < (info[0] - 250) < 10:
                    self.add_info(_("Unverified address: %(info)s."
                                  " But mail will be sent anyway.") % d)
                else:
                    self.add_warning(_("Unverified address: %(info)s.") % d,
                     tag=WARN_MAIL_UNVERIFIED_ADDRESS)
            except smtplib.SMTPException, msg:
                self.add_warning(
                      _("MX mail host %(host)s did not accept connections: "
                        "%(error)s.") % {'host': host, 'error': str(msg)},
                        tag=WARN_MAIL_NO_CONNECTION)
            if smtpconnect:
                break
        if not smtpconnect:
            self.set_result(_("Could not connect, but syntax is correct"))
        else:
            self.set_result(_("Found MX mail host %(host)s") % {'host': host})

    def close_connection (self):
        """
        Close a possibly opened SMTP connection.
        """
        if self.url_connection is None:
            # no connection is open
            return
        connection = self.url_connection
        self.url_connection = None
        try:
            connection.quit()
        except smtplib.SMTPException:
            # ignore close errors
            pass

    def set_cache_keys (self):
        """
        The cache key is a comma separated list of emails.
        """
        emails = u",".join(sorted(addr[1] for addr in self.addresses))
        self.cache_url_key = u"%s:%s" % (self.scheme, emails)
        assert isinstance(self.cache_url_key, unicode), self.cache_url_key
        # cache_content_key remains None, recursion is not allowed

    def can_get_content (self):
        """
        mailto: URLs do not have any content

        @return: False
        @rtype: bool
        """
        return False
