import socket,string
from UrlData import UrlData

class HostCheckingUrlData(UrlData):
    "Url link for which we have to connect to a specific host"

    def __init__(self,
                 urlName, 
                 recursionLevel, 
                 parentName = None,
                 baseRef = None, line=0):
        UrlData.__init__(self, urlName, recursionLevel,
	                 parentName=parentName, baseRef=baseRef, line=line)
        self.host = None
        self.url = urlName

    def buildUrl(self):
        # to avoid anchor checking
        self.urlTuple=None
        
    def getCacheKey(self):
        return self.host

    def checkConnection(self, config):
        ip = socket.gethostbyname(self.host)
        self.setValid(self.host+"("+ip+") found")

    def __str__(self):
        return "host="+`self.host`+"\n"+UrlData.__str__(self)

