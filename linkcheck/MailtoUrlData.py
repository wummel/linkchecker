"""Handle for mailto: links"""
# Copyright (C) 2000,2001  Bastian Kleineidam
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

import os, re, DNS, sys, Config, cgi, urllib, linkcheck
from rfc822 import AddressList
from HostCheckingUrlData import HostCheckingUrlData
from smtplib import SMTP
from debuglevels import *

# regular expression for RFC2368 compliant mailto: scanning
headers_re = re.compile(r"\?(.+)$")

# parse /etc/resolv.conf (on UNIX systems)
# or read entries from the registry (Windows systems)
DNS.init_dns_resolver()

class MailtoUrlData(HostCheckingUrlData):
    "Url link with mailto scheme"

    def buildUrl(self):
        HostCheckingUrlData.buildUrl(self)
        self.headers = {}
        self.adresses = AddressList(self._cutout_adresses()).addresslist
        for key in ("to","cc","bcc"):
            if self.headers.has_key(key):
                for val in self.headers[key]:
                    a = urllib.unquote(val)
                    self.adresses.extend(AddressList(a).addresslist)
        Config.debug(BRING_IT_ON, "mailto headers:", self.headers)


    def _cutout_adresses(self):
        mo = headers_re.search(self.urlName)
        if mo:
            self.headers = cgi.parse_qs(mo.group(1), strict_parsing=1)
            return self.urlName[7:mo.start()]
        return self.urlName[7:]


    def checkConnection(self, config):
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
            self.setWarning(linkcheck._("No adresses found"))
            return

        value = "unknown reason"
        for name,mail in self.adresses:
            Config.debug(BRING_IT_ON, "checking mail address", mail)
            Config.debug(HURT_ME_PLENTY, "splitting address")
            user,host = self._split_adress(mail)
            Config.debug(HURT_ME_PLENTY, "looking up MX mailhost")
            mxrecords = DNS.mxlookup(host, protocol="tcp")
            Config.debug(HURT_ME_PLENTY, "found mailhosts", mxrecords)
            if not len(mxrecords):
                self.setError(linkcheck._("No mail host for %s found")%host)
                return
            smtpconnect = 0
            for mxrecord in mxrecords:
                try:
                    Config.debug(BRING_IT_ON, "SMTP check for", mxrecord)
                    self.urlConnection = SMTP(mxrecord[1])
                    Config.debug(HURT_ME_PLENTY, "SMTP connected!")
                    smtpconnect = 1
                    self.urlConnection.helo()
                    info = self.urlConnection.verify(user)
                    Config.debug(HURT_ME_PLENTY, "SMTP user info", info)
                    if info[0]==250:
                        self.setInfo(linkcheck._("Verified adress: %s")%str(info[1]))
                except:
                    type, value = sys.exc_info()[:2]
                    #print type,value
                if smtpconnect: break
            
            if not smtpconnect:
                self.setWarning(linkcheck._("None of the mail hosts for %s accepts an "
                                  "SMTP connection: %s") % (host, str(value)))
                mxrecord = mxrecords[0][1]
            else:
                mxrecord = mxrecord[1]
            self.setValid(linkcheck._("found mail host %s") % mxrecord)


    def _split_adress(self, adress):
        split = adress.split("@", 1)
        if len(split)==2:
            if not split[1]:
                return (split[0], "localhost")
            return tuple(split)
        if len(split)==1:
            return (split[0], "localhost")
        raise linkcheck.error, linkcheck._("could not split the mail adress")


    def closeConnection(self):
        try: self.urlConnection.quit()
        except: pass
        self.urlConnection = None


    def getCacheKey(self):
        return "%s:%s" % (self.scheme, str(self.adresses))
