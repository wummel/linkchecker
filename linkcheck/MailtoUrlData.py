import re,socket,string,DNS,sys
from HostCheckingUrlData import HostCheckingUrlData
from smtplib import SMTP

class MailtoUrlData(HostCheckingUrlData):
    "Url link with mailto scheme"
    
    def buildUrl(self):
        HostCheckingUrlData.buildUrl(self)
        if not re.compile("^mailto:([\-\w.]+@[\-\w.?=]+|[\w\s]+<[\-\w.]+@[\-\w.?=]+>)").match(self.urlName):
            raise Exception, "Illegal mailto link syntax"
        self.host = self.urlName[7:]
        i = string.find(self.host, "<")
        j = string.find(self.host, ">")
        if i!=-1 and j!=-1 and i<j:
            self.host = self.host[i+1:j]
        i = string.find(self.host, "@")
        self.user = self.host[:i]
        self.host = self.host[(i+1):]
        i = string.find(self.host, "?")
        if i!=-1:
            self.host = self.host[:i]
        self.host = string.lower(self.host)
        # do not lower the user name

    def checkConnection(self, config):
        DNS.ParseResolvConf()
        mxrecords = DNS.mxlookup(self.host)
        if not len(mxrecords):
            self.setError("No mail host for "+self.host+" found")
            return
        smtpconnect = 0
        for mxrecord in mxrecords:
            try:
                self.urlConnection = SMTP(mxrecord[1])
                smtpconnect = 1
                self.urlConnection.helo()
                info = self.urlConnection.verify(self.user)
                if info[0]==250:
                    self.setInfo("Verified adress: "+info[1])
            except:
                type, value = sys.exc_info()[:2]
                #print value
            if smtpconnect: break
            
        if not smtpconnect:
            self.setWarning("None of the mail hosts for "+self.host+" accepts an SMTP connection")
            mxrecord = mxrecords[0][1]
        else:
            mxrecord = mxrecord[1]
        self.setValid("found mail host "+mxrecord)


    def closeConnection(self):
        try: self.urlConnection.quit()
        except: pass
        self.urlConnection = None


    def getCacheKey(self):
        return "mailto:"+self.user+"@"+HostCheckingUrlData.getCacheKey(self)


    def __str__(self):
        return "Mailto link\n"+HostCheckingUrlData.__str__(self)


