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
import rfc822
import linkcheck
import linkcheck.checker.HostCheckingUrlData
import bk.log
import bk.i18n
import bk.net.dns.lazy

# regular expression for RFC2368 compliant mailto: scanning
headers_re = re.compile(r"\?(.+)$")

class MailtoUrlData (linkcheck.checker.HostCheckingUrlData.HostCheckingUrlData):
    "Url link with mailto scheme"

    def buildUrl (self):
        super(MailtoUrlData, self).buildUrl()
        self.headers = {}
        self.adresses = rfc822.AddressList(self._cutout_adresses()).addresslist
        for key in ("to", "cc", "bcc"):
            if self.headers.has_key(key):
                for val in self.headers[key]:
                    a = urllib.unquote(val)
                    self.adresses.extend(rfc822.AddressList(a).addresslist)
        bk.log.debug(BRING_IT_ON, "adresses: ", self.adresses)

    def _cutout_adresses (self):
        mo = headers_re.search(self.urlName)
        if mo:
            headers = cgi.parse_qs(mo.group(1), strict_parsing=True)
            for key, val in headers.items():
                key = key.lower()
                self.headers.setdefault(key, []).extend(val)
            return self.urlName[7:mo.start()]
        return self.urlName[7:]

    def checkConnection (self):
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
            self.setWarning(bk.i18n._("No adresses found"))
            return

        value = "unknown reason"
        for name,mail in self.adresses:
            bk.log.debug(BRING_IT_ON, "checking mail address", mail)
            bk.log.debug(HURT_ME_PLENTY, "splitting address")
            user,host = self._split_adress(mail)
            bk.log.debug(HURT_ME_PLENTY, "looking up MX mailhost")
            mxrecords = bk.net.dns.lazy.mxlookup(host, config.dnsconfig)
            bk.log.debug(HURT_ME_PLENTY, "found mailhosts", mxrecords)
            if not len(mxrecords):
                self.setWarning(bk.i18n._("No MX mail host for %s found")%host)
                return
            smtpconnect = 0
            for mxrecord in mxrecords:
                try:
                    bk.log.debug(BRING_IT_ON, "SMTP check for", mxrecord)
                    self.urlConnection = smtplib.SMTP(mxrecord[1])
                    bk.log.debug(HURT_ME_PLENTY, "SMTP connected!")
                    smtpconnect = 1
                    self.urlConnection.helo()
                    info = self.urlConnection.verify(user)
                    bk.log.debug(HURT_ME_PLENTY, "SMTP user info", info)
                    if info[0]==250:
                        self.setInfo(bk.i18n._("Verified adress: %s")%str(info[1]))
                except:
                    etype, value = sys.exc_info()[:2]
                    #print etype,value
                if smtpconnect: break
            if not smtpconnect:
                self.setWarning(bk.i18n._("None of the MX mail hosts for %s accepts an "
                                  "SMTP connection: %s") % (host, str(value)))
                mxrecord = mxrecords[0][1]
            else:
                mxrecord = mxrecord[1]
            self.setValid(bk.i18n._("found MX mail host %s") % mxrecord)

    def _split_adress (self, adress):
        split = adress.split("@", 1)
        if len(split)==2:
            if not split[1]:
                return (split[0], "localhost")
            return tuple(split)
        if len(split)==1:
            return (split[0], "localhost")
        raise linkcheck.LinkCheckerError(bk.i18n._("could not split the mail adress"))

    def closeConnection (self):
        try: self.urlConnection.quit()
        except: pass
        self.urlConnection = None

    def getCacheKeys (self):
        return ["%s:%s" % (self.scheme, str(self.adresses))]

    def hasContent (self):
        return False

