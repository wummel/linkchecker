# -*- coding: iso-8859-1 -*-
"""Handle for mailto: links"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

import re
import sys
import cgi
import urllib
import smtplib
import email.Utils

import linkcheck
import urlconnect
import linkcheck.log
import linkcheck.dns.resolver

from linkcheck.i18n import _


class MailtoUrl (urlconnect.UrlConnect):
    """Url link with mailto scheme"""

    def build_url (self):
        super(MailtoUrl, self).build_url()
        self.headers = {}
        self.adresses = email.Utils.getaddresses([self.cutout_adresses()])
        for key in ("to", "cc", "bcc"):
            if self.headers.has_key(key):
                for val in self.headers[key]:
                    a = urllib.unquote(val)
                    self.adresses.extend(email.Utils.getaddresses([a]))
        # check syntax of emails
        for name, addr in self.adresses:
            username, domain = addr.split('@')
            if not linkcheck.url.is_valid_domain(domain):
                raise linkcheck.LinkCheckerError(_("Invalid mail syntax"))
        linkcheck.log.debug(linkcheck.LOG_CHECK, "adresses: %s",
                            self.adresses)

    def cutout_adresses (self):
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
        """Verify a list of email adresses. If one adress fails,
        the whole list will fail.
        For each mail adress we check the following things:
        (1) Look up the MX DNS records. If we found no MX record,
            print an error.
        (2) Check if one of the mail hosts accept an SMTP connection.
            Check hosts with higher priority first.
            If no host accepts SMTP, we print a warning.
        (3) Try to verify the adress with the VRFY command. If we got
            an answer, print the verified adress as an info.
        """
        if not self.adresses:
            self.add_warning(_("No adresses found"))
            return

        value = "unknown reason"
        for name, mail in self.adresses:
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "checking mail address %r", mail)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "splitting address")
            user, host = self._split_adress(mail)
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "looking up MX mailhost %r", host)
            answers = linkcheck.dns.resolver.query(host, 'MX')
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "found %d MX mailhosts", len(answers))
            if len(answers) == 0:
                self.add_warning(_("No MX mail host for %(host)s found") % \
                                {'host': host})
                return
            smtpconnect = 0
            for rdata in answers:
                try:
                    host = rdata.exchange.to_text(omit_final_dot=True)
                    preference = rdata.preference
                    linkcheck.log.debug(linkcheck.LOG_CHECK,
                              "SMTP check for %r (pref %d)", host, preference)
                    self.url_connection = smtplib.SMTP(host)
                    linkcheck.log.debug(linkcheck.LOG_CHECK,
                                        "SMTP connected!")
                    smtpconnect = 1
                    self.url_connection.helo()
                    info = self.url_connection.verify(user)
                    linkcheck.log.debug(linkcheck.LOG_CHECK,
                                        "SMTP user info %r", info)
                    if info[0] == 250:
                        self.add_info(_("Verified adress: %(info)s") % \
                                     {'info': str(info[1])})
                except:
                    etype, value = sys.exc_info()[:2]
                    self.add_warning(
                      _("MX mail host %(host)s did not accept connections: "\
                        "%(error)s") % \
                        {'host': rdata.exchange, 'error': str(value)})
                if smtpconnect:
                    break
            if not smtpconnect:
                self.set_result(_("Could not connect, but syntax is correct"))
            else:
                self.set_result(_("Found MX mail host %(host)s") % \
                              {'host': rdata.exchange})

    def _split_adress (self, adress):
        split = adress.split("@", 1)
        if len(split) == 2:
            if not split[1]:
                return (split[0], "localhost")
            return tuple(split)
        if len(split) == 1:
            return (split[0], "localhost")
        raise linkcheck.LinkCheckerError(_("could not split the mail adress"))

    def close_connection (self):
        try: self.url_connection.quit()
        except: pass
        self.url_connection = None

    def get_cache_keys (self):
        return ["%s:%s" % (self.scheme, str(self.adresses))]

    def can_get_content (self):
        return False
