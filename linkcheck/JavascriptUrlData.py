from UrlData import UrlData

class JavascriptUrlData(UrlData):
    "Url link with javascript scheme"

    def check(self, config):
        self.setWarning("Javascript url ignored")
        self.logMe(config)

    def __str__(self):
        return "Javascript link\n"+UrlData.__str__(self)
    
    
