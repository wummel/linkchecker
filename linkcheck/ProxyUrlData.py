from UrlData import UrlData
from urllib import splittype, splithost, splituser

class ProxyUrlData (UrlData):
    """urldata with ability for proxying and for urls with user:pass@host
       setting"""

    def setProxy (self, proxy):
        self.proxy = proxy
        self.proxyauth = None
        if self.proxy:
            if self.proxy[:7].lower() != "http://":
                self.proxy = "http://"+self.proxy
            self.proxy = splittype(self.proxy)[1]
            self.proxy = splithost(self.proxy)[0]
            self.proxyauth, self.proxy = splituser(self.proxy)
            if self.proxyauth is not None:
                if ":" not in self.proxyauth: self.proxyauth += ":"
                import base64
                self.proxyauth = base64.encodestring(self.proxyauth).strip()
                self.proxyauth = "Basic "+self.proxyauth

