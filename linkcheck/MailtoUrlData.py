"""
    Copyright (C) 2000  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
import re,string,DNS,sys,Config,cgi,urllib
from rfc822 import AddressList
from HostCheckingUrlData import HostCheckingUrlData
from smtplib import SMTP
from UrlData import LinkCheckerException


# regular expression for RFC2368 compliant mailto: scanning
word = r"[-a-zA-Z0-9,./%]+"
headers = r"\?(%s=%s(&%s=%s)*)$" % (word, word, word, word)
headers_re = re.compile(headers)

class MailtoUrlData(HostCheckingUrlData):
    "Url link with mailto scheme"
    
    def buildUrl(self):
        HostCheckingUrlData.buildUrl(self)
        self.headers = {}
        self.adresses = AddressList(self._cutout_adresses()).addresslist
        for key in ["to","cc","bcc"]:
            if self.headers.has_key(key):
                for val in self.headers[key]:
                    a = urllib.unquote(val)
                    self.adresses.extend(AddressList(a).addresslist)
        Config.debug("DEBUG: %s\nDEBUG: %s\n" % (self.adresses, self.headers))


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
            self.setWarning("No adresses found")
            return

        DNS.ParseResolvConf()
        for name,mail in self.adresses:
            user,host = self._split_adress(mail)
            mxrecords = DNS.mxlookup(host)
            if not len(mxrecords):
                self.setError("No mail host for "+host+" found")
                return
            smtpconnect = 0
            for mxrecord in mxrecords:
                try:
                    self.urlConnection = SMTP(mxrecord[1])
                    smtpconnect = 1
                    self.urlConnection.helo()
                    info = self.urlConnection.verify(user)
                    if info[0]==250:
                        self.setInfo("Verified adress: "+info[1])
                except:
                    type, value = sys.exc_info()[:2]
                    print type,value
                if smtpconnect: break
            
            if not smtpconnect:
                self.setWarning("None of the mail hosts for "+host+
                                " accepts an SMTP connection: "+str(value))
                mxrecord = mxrecords[0][1]
            else:
                mxrecord = mxrecord[1]
            self.setValid("found mail host "+mxrecord)


    def _split_adress(self, adress):
        split = string.split(adress, "@", 1)
        if len(split)==2:
            if not split[1]:
                return (split[0], "localhost")
            return tuple(split)
        if len(split)==1:
            return (split[0], "localhost")
        raise LinkCheckerException, "could not split the mail adress"


    def closeConnection(self):
        try: self.urlConnection.quit()
        except: pass
        self.urlConnection = None


    def getCacheKey(self):
        return "mailto:"+str(self.adresses)


    def __str__(self):
        return "Mailto link\n"+HostCheckingUrlData.__str__(self)


