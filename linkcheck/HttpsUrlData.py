from UrlData import UrlData
from HttpUrlData import HttpUrlData
_supportHttps=1
try: import httpslib
except: _supportHttps=0

class HttpsUrlData(HttpUrlData):
    """Url link with https scheme"""

    def __init__(self,
                 urlName,
                 recursionLevel, 
                 parentName = None,
                 baseRef = None,
                 line = 0):
        HttpUrlData.__init__(self, urlName, recursionLevel,
                             parentName, baseRef, line)

    def _getHTTPObject(self, host):
        return httpslib.HTTPS(host)

    def check(self, config):
        if _supportHttps:
            HttpUrlData.check(self, config)
        else:
            self.setWarning("HTTPS url ignored")
            self.logMe(config)

    def __str__(self):
        return "HTTPS link\n"+UrlData.__str__(self)
