import re,socket,string,DNS,sys,Config
from HostCheckingUrlData import HostCheckingUrlData
from smtplib import SMTP
from UrlData import LinkCheckerException

# regular expression strings
tag_str = r"^mailto:"
adress_str = r"([a-zA-Z]['\-\w.]*)@([\w\-]+(\.[\w\-]+)*))"
complete_adress_str = "("+adress_str+"|[\w\-\s]*<"+adress_str+">)"
suffix_str = r"(\?.+)?"
mailto_str = tag_str+complete_adress_str+\
             "(\s*,"+complete_adress_str+")*"+suffix_str

# compiled
mailto_re = re.compile(mailto_str)
adress_re = re.compile(adress_str)

class MailtoUrlData(HostCheckingUrlData):
    "Url link with mailto scheme"
    
    def buildUrl(self):
        HostCheckingUrlData.buildUrl(self)
        mo = mailto_re.match(self.urlName)
        if not mo:
            raise LinkCheckerException, "Illegal mailto link syntax"
        self.adresses = re.findall(adress_re, self.urlName)
        Config.debug(str(self.adresses))
        raise Exception, "Nix"
        self.host = None
        self.user = None

    def checkConnection(self, config):
        DNS.ParseResolvConf()
        Config.debug("Looking up mail host\n")
        mxrecords = DNS.mxlookup(self.host)
        if not len(mxrecords):
            self.setError("No mail host for "+self.host+" found")
            return
        smtpconnect = 0
        for mxrecord in mxrecords:
            try:
                Config.debug("Connect to "+str(mxrecord)+"\n")
                self.urlConnection = SMTP(mxrecord[1])
                Config.debug("Connected to "+str(mxrecord[1])+"\n")
                smtpconnect = 1
                self.urlConnection.helo()
                info = self.urlConnection.verify(self.user)
                if info[0]==250:
                    self.setInfo("Verified adress: "+info[1])
            except:
                type, value = sys.exc_info()[:2]
                print type,value
            if smtpconnect: break
            
        if not smtpconnect:
            self.setWarning("None of the mail hosts for "+self.host+
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
        return "mailto:"+self.user+"@"+HostCheckingUrlData.getCacheKey(self)


    def __str__(self):
        return "Mailto link\n"+HostCheckingUrlData.__str__(self)


