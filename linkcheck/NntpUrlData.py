import re,string,time,nntplib,sys
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
        timeout = 1
        while timeout:
            try:
                resp,count,first,last,name = nntp.group(self.host)
                timeout = 0
            except nntplib.error_perm:
                type,value = sys.exc_info()[:2]
                print value
                if value[0]==505:
                    # 505 too many connections per minute
                    import random
                    time.sleep(random.randint(30,60))
                    # try again
                    timeout = 1
                else:
                    raise
        self.setInfo("Group %s has %s articles, range %s to %s" % \
                     (name, count, first, last))


    def getCacheKey(self):
        return "news:"+HostCheckingUrlData.getCacheKey(self)


    def __str__(self):
        return "NNTP link\n"+HostCheckingUrlData.__str__(self)

