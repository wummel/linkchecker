import telnetlib,re
from HostCheckingUrlData import HostCheckingUrlData

class TelnetUrlData(HostCheckingUrlData):
    "Url link with telnet scheme"
    
    def buildUrl(self):
        HostCheckingUrlData.buildUrl(self)
        if not re.compile("^telnet:[\w.\-]+").match(self.urlName):
            raise Exception, "Illegal telnet link syntax"
        self.host = string.lower(self.urlName[7:])


    def checkConnection(self, config):
        HostCheckingUrlData.checkConnection(self, config)
        self.urlConnection = telnetlib.Telnet()
        self.urlConnection.open(self.host, 23)


    def getCacheKey(self):
        return "telnet:"+HostCheckingUrlData.getCacheKey(self)


    def __str__(self):
        return "Telnet link\n"+HostCheckingUrlData.__str__(self)

