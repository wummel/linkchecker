import re,string
from HostCheckingUrlData import HostCheckingUrlData
from UrlData import LinkCheckerException

nntp_re =  re.compile("^news:[\w.\-]+$")

class NntpUrlData(HostCheckingUrlData):
    "Url link with NNTP scheme"
    
    def buildUrl(self):
        HostCheckingUrlData.buildUrl(self)
        if not nntp_re.match(self.urlName):
            raise LinkCheckerException, "Illegal NNTP link syntax"
        self.host = string.lower(self.urlName[5:])


    def checkConnection(self, config):
        if not config["nntpserver"]:
            self.setWarning("No NNTP server specified, checked only syntax")
        config.connectNntp()
        nntp = config["nntp"]
        import time
        time.sleep(10)
        resp,count,first,last,name = nntp.group(self.host)
        self.setInfo("Group %s has %s articles, range %s to %s" % \
                     (name, count, first, last))


    def getCacheKey(self):
        return "news:"+HostCheckingUrlData.getCacheKey(self)


    def __str__(self):
        return "NNTP link\n"+HostCheckingUrlData.__str__(self)

