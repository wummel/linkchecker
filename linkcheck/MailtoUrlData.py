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
import re,socket,string,DNS,sys,Config
from HostCheckingUrlData import HostCheckingUrlData
from smtplib import SMTP
from UrlData import LinkCheckerException

# regular expression strings for partially RFC822 compliant adress scanning
# XXX far from complete mail adress scanning; enhance only when needed!
word = r"[\w\-%']+"
words = r"[\w\-%'\s]+"
dotwords = "("+word+r"(?:\."+word+")*)
adress = dotwords+"@"+dotwords
route_adress = words+"<"+adress+">"
mailbox = "("+adress+"|"+route_adress+")"
mailboxes = mailbox+r"?(,+"+mailbox+")*"

# regular expression strings for RFC2368 compliant mailto: scanning
header = word+"="+word
headers = "?"+header+"(&"+header+")*
mailto = "^mailto:"+mailboxes+headers

# compiled
adress_re = re.compile(adress)
mailto_re = re.compile(mailto)

class MailtoUrlData(HostCheckingUrlData):
    "Url link with mailto scheme"
    
    def buildUrl(self):
        HostCheckingUrlData.buildUrl(self)
        mo = mailto_re.match(self.urlName)
        if not mo:
            raise LinkCheckerException, "Illegal mailto link syntax"
        # note: this catches also cc= headers and such!
        self.adresses = map(lambda x: (x[0], string.lower(x[1])),
	                    re.findall(adress_re, self.urlName))

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
        DNS.ParseResolvConf()
        for user,host in self.adresses:
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


    def closeConnection(self):
        try: self.urlConnection.quit()
        except: pass
        self.urlConnection = None


    def getCacheKey(self):
        return "mailto:"+str(self.adresses)


    def __str__(self):
        return "Mailto link\n"+HostCheckingUrlData.__str__(self)


