# -*- coding: iso-8859-1 -*-
"""Handle for mailto: links"""
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

import sys
import cgi
import urllib
import smtplib
import email.Utils

import linkcheck
import urlbase
import linkcheck.log
import linkcheck.dns.resolver


class MailtoUrl (urlbase.UrlBase):
    """Url link with mailto scheme"""

    def build_url (self):
        super(MailtoUrl, self).build_url()
        self.headers = {}
        self.addresses = email.Utils.getaddresses([self.cutout_addresses()])
        for key in ("to", "cc", "bcc"):
            if self.headers.has_key(key):
                for val in self.headers[key]:
                    a = urllib.unquote(val)
                    self.addresses.extend(email.Utils.getaddresses([a]))
        # check syntax of emails
        for name, addr in self.addresses:
            username, domain = self._split_address(addr)
            if not linkcheck.url.is_safe_domain(domain):
                raise linkcheck.LinkCheckerError(_("Invalid mail syntax"))
        linkcheck.log.debug(linkcheck.LOG_CHECK, "addresses: %s",
                            self.addresses)

    def cutout_addresses (self):
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
            headers = cgi.parse_qs(url[(i+1):], strict_parsing=True)
            for key, val in headers.items():
                key = key.lower()
                self.headers.setdefault(key, []).extend(val)
            addrs = url[:i]
        else:
            addrs = url
        # addrs is comma-separated list of mails now
        return addrs

    def check_connection (self):
        """Verify a list of email addresses. If one address fails,
        the whole list will fail.
        For each mail address we check the following things:
        (1) Look up the MX DNS records. If we found no MX record,
            print an error.
        (2) Check if one of the mail hosts accept an SMTP connection.
            Check hosts with higher priority first.
            If no host accepts SMTP, we print a warning.
        (3) Try to verify the address with the VRFY command. If we got
            an answer, print the verified address as an info.
        """
        if not self.addresses:
            self.add_warning(_("No addresses found."))
            return

        value = "unknown reason"
        for name, mail in self.addresses:
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "checking mail address %r", mail)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "splitting address")
            username, domain = self._split_address(mail)
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "looking up MX mailhost %r", domain)
            answers = linkcheck.dns.resolver.query(domain, 'MX')
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "found %d MX mailhosts", len(answers))
            if len(answers) == 0:
                self.add_warning(_("No MX mail host for %(domain)s found.") %\
                                {'domain': domain})
                return
            smtpconnect = 0
            for rdata in answers:
                try:
                    host = rdata.exchange.to_text(omit_final_dot=True)
                    preference = rdata.preference
                    linkcheck.log.debug(linkcheck.LOG_CHECK,
                              "SMTP check for %r (pref %d)", host, preference)
                    self.url_connection = smtplib.SMTP()
                    if self.consumer.config.get("debug"):
                        self.url_connection.set_debuglevel(1)
                    self.url_connection.connect(host)
                    linkcheck.log.debug(linkcheck.LOG_CHECK,
                                        "SMTP connected!")
                    smtpconnect = 1
                    self.url_connection.helo()
                    info = self.url_connection.verify(username)
                    linkcheck.log.debug(linkcheck.LOG_CHECK,
                                        "SMTP user info %r", info)
                    if info[0] == 250:
                        self.add_info(_("Verified address: %(info)s.") % \
                                     {'info': str(info[1])})
                except smtplib.SMTPException, msg:
                    self.add_warning(
                      _("MX mail host %(host)s did not accept connections: "\
                        "%(error)s.") % \
                        {'host': rdata.exchange, 'error': str(msg)})
                if smtpconnect:
                    break
            if not smtpconnect:
                self.set_result(_("Could not connect, but syntax is correct"))
            else:
                self.set_result(_("Found MX mail host %(host)s") % \
                              {'host': rdata.exchange})

    def _split_address (self, address):
        split = address.split("@", 1)
        if len(split) == 2:
            if not split[1]:
                return (split[0], "localhost")
            return tuple(split)
        if len(split) == 1:
            return (split[0], "localhost")
        raise linkcheck.LinkCheckerError(
                                  _("Could not split the mail address"))

    def close_connection (self):
        """close a possibly opened SMTP connection"""
        if self.url_connection is None:
            # no connection is open
            return
        try:
            self.url_connection.quit()
        except smtplib.SMTPException:
            pass
        self.url_connection = None

    def set_cache_keys (self):
        """The cache key is a comma separated list of emails."""
        emails = [addr[1] for addr in self.addresses]
        emails.sort()
        self.cache_url_key = u"%s:%s" % (self.scheme, u",".join(emails))
        assert isinstance(self.cache_url_key, unicode), self.cache_url_key
        # cache_content_key remains None, recursion is not allowed

    def can_get_content (self):
        """mailto: URLs do not have any content
           @return False
        """
        return False
