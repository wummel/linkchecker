import re,string,os,urlparse
from UrlData import UrlData
from os.path import normpath

class FileUrlData(UrlData):
    "Url link with file scheme"

    def __init__(self,
                 urlName, 
                 recursionLevel, 
                 parentName = None,
                 baseRef = None, line=0, _time=0):
        UrlData.__init__(self,
                 urlName, 
                 recursionLevel, 
                 parentName,
                 baseRef, line, _time)
        if not parentName and not baseRef and \
           not re.compile("^file:").search(self.urlName):
            winre = re.compile("^[a-zA-Z]:")
            if winre.search(self.urlName):
                self.adjustWinPath()
            else:
                if self.urlName[0:1] != "/":
                    self.urlName = os.getcwd()+"/"+self.urlName
                    if winre.search(self.urlName):
                        self.adjustWindozePath()
            self.urlName = "file://"+normpath(self.urlName)


    def buildUrl(self):
        UrlData.buildUrl(self)
        # cut off parameter, query and fragment
        self.url = urlparse.urlunparse(self.urlTuple[:3] + ('','',''))


    def adjustWinPath(self):
        "c:\\windows ==> /c|\\windows"
        self.urlName = "/"+self.urlName[0]+"|"+self.urlName[2:]


    def isHtml(self):
        return self.valid and re.compile("\.s?html?$").search(self.url)


    def __str__(self):
        return "File link\n"+UrlData.__str__(self)

