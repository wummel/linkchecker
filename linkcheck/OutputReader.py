import string,re
import UrlData

class ParseException(Exception):
    pass
    
class OutputReader:

    ws = re.compile("\s+")
    regex_realUrl = re.compile("^Real URL.+")
    regex_result = re.compile("^Result.+")
    regex_base = re.compile("^Base.+")
    regex_info = re.compile("^Info.+")
    regex_warning = re.compile("^Warning.+") 
    regex_parentUrl = re.compile("^Parent URL.+")
    regex_valid = re.compile("^Valid.*")

    def resetState(self):
        self.urlName = None
        self.parentName = None
        self.baseRef = None
        self.info = None
        self.warning = None
        self.result = None
        self.linenumber = 0
        self.state = 0

    def parse(self, file):
        line = file.readline()
        url = None
        urls = []
        self.resetState()

        while line:
            if OutputReader.ws.match(line):
                if self.state>=2: 
                    #append url
                    urldata = UrlData.GetUrlDataFrom(self.urlName, 0, 
                    self.parentName, self.baseRef, self.linenumber)
                    if self.info:
                        urldata.setInfo(self.info)
                    if self.warning:
                        urldata.setWarning(self.info)
                    if OutputReader.regex_valid.match(self.result):
                        urldata.valid=1
                        urldata.validString = self.result
                    else:
                        urldata.valid=0
                        urldata.errorString = self.result
                    urls.append(urldata)
                elif self.state:
                    raise ParseException, "No Real URL and Result keyword found"
                self.resetState()
                
            elif OutputReader.regex_realUrl.match(line): 
                self.state = self.state+1
                self.urlName = string.strip(line[8:])
            elif OutputReader.regex_result.match(line): 
                self.state = self.state+1
                self.result = string.strip(line[6:])
            elif OutputReader.regex_info.match(line):
                self.info = string.strip(line[4:])
            elif OutputReader.regex_base.match(line):
                self.baseRef = string.strip(line[4:])
            elif OutputReader.regex_warning.match(line):
                self.warning = string.strip(line[7:])
            elif OutputReader.regex_parentUrl.match(line):
                self.parentName = string.strip(line[10:])
                if ',' in self.parentName:
                    self.parentName,self.linenumber = string.split(self.parentName,",",1)
            else:
                pass
                
            line = file.readline()
        return urls

