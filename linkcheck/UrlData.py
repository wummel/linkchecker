import sys,re,string,urlparse,urllib,time
import Config,StringUtil

LinkTags = [("a",     "href"),
            ("img",   "src"),
            ("form",  "action"),
            ("body",  "background"),
            ("frame", "src"),
            ("link",  "href"),
            # <meta http-equiv="refresh" content="5; url=...">
            ("meta",  "url"),  
            ("area",  "href")]

class LinkCheckerException(Exception):
    pass

class UrlData:
    "Representing a URL with additional information like validity etc"
    
    def __init__(self, 
                 urlName, 
                 recursionLevel, 
                 parentName = None,
                 baseRef = None,
                 line = None):
        self.urlName = urlName
        self.recursionLevel = recursionLevel
        self.parentName = parentName
        self.baseRef = baseRef
        self.errorString = "Error"
        self.validString = "Valid"
        self.warningString = None
        self.infoString = None
        self.valid = 1
        self.url = None
        self.line = line
        self.downloadtime = None
        self.checktime = None
        self.cached = 0
        self.urlConnection = None
        self.extern = 1
        self.data = None
        
        
    def setError(self, s):
        self.valid=0
        self.errorString = "Error: " + s
        
    def setValid(self, s):
        self.valid=1
        self.validString = "Valid: " + s
        
    def isHtml(self):
        return 0
        
    def setWarning(self, s):
        if self.warningString:
            self.warningString = self.warningString+"\n" + s
        else:
            self.warningString = s

    def setInfo(self, s):
        if self.infoString:
            self.infoString = self.infoString+"\n"+s
        else:
            self.infoString = s
            
    def copyFrom(self, urlData):
        self.errorString = urlData.errorString
        self.validString = urlData.validString
        self.warningString = urlData.warningString
        self.infoString = urlData.infoString
        self.valid = urlData.valid
        self.downloadtime = urlData.downloadtime

    def buildUrl(self):
        if self.baseRef:
            self.url = urlparse.urljoin(self.baseRef, self.urlName)
        elif self.parentName:
            self.url = urlparse.urljoin(self.parentName, self.urlName)
        else: 
            self.url = self.urlName
        self.urlTuple = urlparse.urlparse(self.url)
        # make host lowercase
        self.urlTuple = (self.urlTuple[0],string.lower(self.urlTuple[1]),
                         self.urlTuple[2],self.urlTuple[3],self.urlTuple[4],
                         self.urlTuple[5])
        self.url = urlparse.urlunparse(self.urlTuple)

    def logMe(self, config):
        if config["verbose"] or not self.valid or \
           (self.warningString and config["warnings"]):
            config.log_newUrl(self)

    def check(self, config):
        Config.debug(Config.DebugDelim+"Checking\n"+str(self)+"\n"+\
                     Config.DebugDelim)
        t = time.time()
        # check syntax
        Config.debug("DEBUG: checking syntax\n")
        if not self.urlName or self.urlName=="":
            self.setError("URL is null or empty")
            self.logMe(config)
            return
        try:
	    self.buildUrl()
            self.extern = self._getExtern(config)
        except LinkCheckerException:
            type, value = sys.exc_info()[:2]
            self.setError(str(value))
            self.logMe(config)
            return

        # check the cache
        Config.debug("DEBUG: checking cache\n")
        if config.urlCache_has_key(self.getCacheKey()):
            self.copyFrom(config.urlCache_get(self.getCacheKey()))
            self.cached = 1
            self.logMe(config)
            return
        
        # apply filter
        Config.debug("DEBUG: checking filter\n")
        if self.extern and (config["strict"] or self.extern[1]):
            self.setWarning("outside of domain filter, checked only syntax")
            self.logMe(config)
            return

        # check connection
        Config.debug("DEBUG: checking connection\n")
        try:
            self.checkConnection(config)
            if self.urlTuple and config["anchors"]:
                self.checkAnchors(self.urlTuple[5])
        # XXX should only catch some exceptions, not all!
        except:
            type, value = sys.exc_info()[:2]
            self.setError(str(value))

        # check content
        warningregex = config["warningregex"]
        if warningregex and self.valid:
            Config.debug("DEBUG: checking content\n")
            self.checkContent(warningregex)

        self.checktime = time.time() - t
        # check recursion
        Config.debug("DEBUG: checking recursion\n")
        if self.allowsRecursion(config):
            self.parseUrl(config)
        self.closeConnection()
        self.logMe(config)
        self.putInCache(config)


    def closeConnection(self):
        # brute force closing
        if self.urlConnection is not None:
            try: self.urlConnection.close()
            except: pass
            # release variable for garbage collection
            self.urlConnection = None

    def putInCache(self, config):
        cacheKey = self.getCacheKey()
        if cacheKey and not self.cached:
            config.urlCache_set(cacheKey, self)
            self.cached = 1

    def getCacheKey(self):
        if self.urlTuple:
            return urlparse.urlunparse(self.urlTuple)
        return None

    def checkConnection(self, config):
        self.urlConnection = urllib.urlopen(self.url)

    def allowsRecursion(self, config):
        return self.valid and \
               self.isHtml() and \
               not self.cached and \
               self.recursionLevel < config["recursionlevel"] and \
               not self.extern

    def isHtml(self):
        return 0

    def checkAnchors(self, anchor):
        if not (anchor!="" and self.isHtml() and self.valid):
            return
        for cur_anchor,line in self.searchInForTag(self.getContent(), ("a", "name")):
            if cur_anchor == anchor:
                return
        self.setWarning("anchor #"+anchor+" not found")

    def _getExtern(self, config):
        if not (config["externlinks"] or config["internlinks"]):
            return 0
        # deny and allow external checking
        Config.debug(self.url)
        if config["allowdeny"]:
            for pat in config["internlinks"]:
                if pat.search(self.url):
                    return 0
            for pat, strict in config["externlinks"]:
                if pat.search(self.url):
                    return (1, strict)
        else:
            for pat, strict in config["externlinks"]:
                if pat.search(self.url):
                    return (1, strict)
            for pat in config["internlinks"]:
                if pat.search(self.url):
                    return 0
        return (1,0)

    def getContent(self):
        """Precondition: urlConnection is an opened URL.
        """
        if not self.data:
            t = time.time()
            self.data = StringUtil.stripHtmlComments(self.urlConnection.read())
            self.downloadtime = time.time() - t

    def checkContent(self, warningregex):
        self.getContent()
        match = warningregex.search(self.data)
        if match:
            self.setWarning("Found '"+match.group()+"' in link contents")
    
    def parseUrl(self, config):
        Config.debug(Config.DebugDelim+"Parsing recursively into\n"+\
                         str(self)+"\n"+Config.DebugDelim)
        self.getContent()
        
        # search for a possible base reference
        bases = self.searchInForTag(self.data, ("base", "href"))
        baseRef = None
        if len(bases)>=1:
            baseRef = bases[0][0]
            if len(bases)>1:
                self.setWarning("more than one base tag found")
            
        # search for tags and add found tags to URL queue
        for tag in LinkTags:
            urls = self.searchInForTag(self.data, tag)
            Config.debug("DEBUG: "+str(tag)+" urls="+str(urls)+"\n")
            for _url,line in urls:
                config.appendUrl(GetUrlDataFrom(_url,
                        self.recursionLevel+1, self.url, baseRef, line))

    def searchInForTag(self, data, tag):
        _urls = []
        _prefix="<\s*"+tag[0]+"\s+[^>]*?"+tag[1]+"\s*=\s*"
        _suffix="[^>]*>"
        _patterns = [re.compile(_prefix+"\"([^\"]+)\""+_suffix, re.I),
                     re.compile(_prefix+"([^\s>]+)"   +_suffix, re.I)]
        cutofflines = 0
        for _pattern in _patterns:
            while 1:
                _match = _pattern.search(data)
                if not _match: break
                # need to strip optional ending quotes for the <meta url=> tag
                linenumberbegin = StringUtil.getLineNumber(data, _match.start(0))
                linenumberend = StringUtil.getLineNumber(data, _match.end(0))
                cutofflines = cutofflines + linenumberend - linenumberbegin
                _urls.append((string.strip(StringUtil.rstripQuotes(_match.group(1))),
                     linenumberbegin + cutofflines))
                data = data[:_match.start(0)] + data[_match.end(0):]
        
        return _urls

    def __str__(self):
        return "urlname="+`self.urlName`+"\nparentName="+`self.parentName`+\
               "\nbaseRef="+`self.baseRef`+"\ncached="+`self.cached`+\
               "\nrecursionLevel="+`self.recursionLevel`+\
               "\nurlConnection="+str(self.urlConnection)+\
	       "\nline="+`self.line`

    def _getUserPassword(self, config):
        for rx, _user, _password in config["authentication"]:
            if rx.match(self.url):
                return _user, _password


from FileUrlData import FileUrlData
from FtpUrlData import FtpUrlData
from GopherUrlData import GopherUrlData
from HttpUrlData import HttpUrlData
from HttpsUrlData import HttpsUrlData
from JavascriptUrlData import JavascriptUrlData
from MailtoUrlData import MailtoUrlData
from TelnetUrlData import TelnetUrlData
from NntpUrlData import NntpUrlData

def GetUrlDataFrom(urlName, 
                   recursionLevel, 
                   parentName = None,
                   baseRef = None, line = 0):
    # search for the absolute url
    name=""
    if urlName and ":" in urlName:
        name = string.lower(urlName)
    elif baseRef and ":" in baseRef:
        name = string.lower(baseRef)
    elif parentName and ":" in parentName:
        name = string.lower(parentName)
    # test scheme
    if re.compile("^http:").search(name):
        return HttpUrlData(urlName, recursionLevel, parentName, baseRef, line)
    if re.compile("^ftp:").search(name):
        return FtpUrlData(urlName, recursionLevel, parentName, baseRef, line)
    if re.compile("^file:").search(name):
        return FileUrlData(urlName, recursionLevel, parentName, baseRef, line)
    if re.compile("^telnet:").search(name):
        return TelnetUrlData(urlName, recursionLevel, parentName, baseRef, line)
    if re.compile("^mailto:").search(name):
        return MailtoUrlData(urlName, recursionLevel, parentName, baseRef, line)
    if re.compile("^gopher:").search(name):
        return GopherUrlData(urlName, recursionLevel, parentName, baseRef, line)
    if re.compile("^javascript:").search(name):
        return JavascriptUrlData(urlName, recursionLevel, parentName, baseRef, line)
    if re.compile("^https:").search(name):
        return HttpsUrlData(urlName, recursionLevel, parentName, baseRef, line)
    if re.compile("^news:").search(name):
        return NntpUrlData(urlName, recursionLevel, parentName, baseRef, line)
    # assume local file
    return FileUrlData(urlName, recursionLevel, parentName, baseRef, line)

