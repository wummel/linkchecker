from UrlData import UrlData

class HttpsUrlData(UrlData):
    "Url link with https scheme"
    
    def check(self, config):
        self.setWarning("Https url ignored")
        self.logMe(config)
    
    def __str__(self):
        return "HTTPS link\n"+UrlData.__str__(self)
    
    
