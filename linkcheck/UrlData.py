"""Base URL handler"""
#    Copyright (C) 2000,2001  Bastian Kleineidam
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import sys,re,string,urlparse,urllib,time,DNS
import Config,StringUtil,linkcheck
from linkcheck import _
debug = linkcheck.Config.debug

ExcList = [
   IOError,
   ValueError, # from httplib.py
   linkcheck.error,
   EOFError, # from ftplib.py
   DNS.Error,
]
try:
    import socket
    ExcList.append(socket.error)
except ImportError:
    pass

_linkMatcher = r"""
    (?i)           # case insensitive
    <              # open tag
    \s*            # whitespace
    %s             # tag name
    \s+            # whitespace
    [^>]*?         # skip leading attributes
    %s             # attrib name
    \s*            # whitespace
    =              # equal sign
    \s*            # whitespace
    (?P<value>     # attribute value
     ".*?" |       # in double quotes
     '.*?' |       # in single quotes
     [^\s>]+)      # unquoted
    ([^">]|".*?")* # skip trailing attributes
    >              # close tag
    """


# ripped mainly from HTML::Tagset.pm
LinkTags = (
    ("a",       ["href"]),
    ("applet",  ["archive", "codebase", "src"]),
    ("area",    ["href"]),
    ("bgsound", ["src"]),
    ("blockquote", ["cite"]),
    ("body",    ["background"]),
    ("del",     ["cite"]),
    ("embed",   ["pluginspage", "src"]),
    ("form",    ["action"]),
    ("frame",   ["src", "longdesc"]),
    ('head',    ['profile']),
    ("iframe",  ["src", "longdesc"]),
    ("ilayer",  ["background"]),
    ("img",     ["src", "lowsrc", "longdesc", "usemap"]),
    ('input',   ['src', 'usemap']),
    ('ins',     ['cite']),
    ('isindex', ['action']),
    ('layer',   ['background', 'src']),
    ("link",    ["href"]),
    ("meta",    ["url"]), # <meta http-equiv="refresh" content="x; url=...">
    ('object',  ['classid', 'codebase', 'data', 'archive', 'usemap']),
    ('q',       ['cite']),
    ('script',  ['src', 'for']),
    ('table',   ['background']),
    ('td',      ['background']),
    ('th',      ['background']),
    ('tr',      ['background']),
    ('xmp',     ['href']),
)

LinkPatterns = []
for tag,attrs in LinkTags:
    for attr in attrs:
        LinkPatterns.append({'pattern': re.compile(_linkMatcher % (tag, attr),
                                                   re.VERBOSE),
                             'tag': tag,
	                     'attr': attr})
AnchorPattern = {
    'pattern': re.compile(_linkMatcher % ("a", "name"), re.VERBOSE),
    'tag': 'a',
    'attr': 'name',
}

BasePattern = {
    'pattern': re.compile(_linkMatcher % ("base", "href"), re.VERBOSE),
    'tag': 'base',
    'attr': 'href',
}

CommentPattern = re.compile("<!--.*?--\s*>", re.DOTALL)

# Workaround for Python 2.0 re module bug
CommentPatternBegin = re.compile("<!--")
CommentPatternEnd = re.compile("--\s*>")

class UrlData:
    "Representing a URL with additional information like validity etc"
    
    def __init__(self, 
                 urlName, 
                 recursionLevel, 
                 parentName = None,
                 baseRef = None,
                 line = 0,
		 name = ""):
        self.urlName = urlName
        self.recursionLevel = recursionLevel
        self.parentName = parentName
        self.baseRef = baseRef
        self.errorString = _("Error")
        self.validString = _("Valid")
        self.warningString = None
        self.infoString = None
        self.valid = 1
        self.url = None
        self.line = line
        self.name = name
        self.downloadtime = 0
        self.checktime = 0
        self.cached = 0
        self.urlConnection = None
        self.extern = 1
        self.data = None
        self.html_comments = []
        self.has_content = 0
        
        
    def setError(self, s):
        self.valid=0
        self.errorString = _("Error")+": "+s
        
    def setValid(self, s):
        self.valid=1
        self.validString = _("Valid")+": "+s
        
    def isHtml(self):
        return 0
        
    def setWarning(self, s):
        if self.warningString:
            self.warningString += "\n" + s
        else:
            self.warningString = s

    def setInfo(self, s):
        if self.infoString:
            self.infoString += "\n"+s
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
        debug("DEBUG: logging url\n")
        config.incrementLinknumber()
        if config["verbose"] or not self.valid or \
           (self.warningString and config["warnings"]):
            config.log_newUrl(self)


    def check(self, config):
        debug(Config.DebugDelim+"Checking\n"+str(self)+"\n"+\
                     Config.DebugDelim)
        t = time.time()
        # check syntax
        debug("DEBUG: checking syntax\n")
        if not self.urlName or self.urlName=="":
            self.setError(_("URL is null or empty"))
            self.logMe(config)
            return
        try:
	    self.buildUrl()
            self.extern = self._getExtern(config)
        except linkcheck.error:
            type, value = sys.exc_info()[:2]
            self.setError(str(value))
            self.logMe(config)
            return

        # check the cache
        debug("DEBUG: checking cache\n")
        if config.urlCache_has_key(self.getCacheKey()):
            self.copyFrom(config.urlCache_get(self.getCacheKey()))
            self.cached = 1
            self.logMe(config)
            return
        
        # apply filter
        debug("DEBUG: checking filter\n")
        debug("DEBUG: extern = %s\n" % str(self.extern))
        if self.extern and (config["strict"] or self.extern[1]):
            self.setWarning(_("outside of domain filter, checked only syntax"))
            self.logMe(config)
            return

        # check connection
        debug("DEBUG: checking connection\n")
        try:
            self.checkConnection(config)
            if self.urlTuple and config["anchors"]:
                self.checkAnchors(self.urlTuple[5])
        except tuple(ExcList):
            type, value = sys.exc_info()[:2]
            self.setError(str(value))

        # check content
        warningregex = config["warningregex"]
        if warningregex and self.valid:
            debug("DEBUG: checking content\n")
            try:  self.checkContent(warningregex)
            except tuple(ExcList):
                type, value = sys.exc_info()[:2]
                self.setError(str(value))

        self.checktime = time.time() - t
        # check recursion
        debug("DEBUG: checking recursion\n")
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
        Config.debug("extern: %s\n" % str(self.extern))
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
        self.getContent()
        for cur_anchor,line,name in self.searchInForTag(AnchorPattern):
            if cur_anchor == anchor:
                return
        self.setWarning("anchor #"+anchor+" not found")


    def _getExtern(self, config):
        if not (config["externlinks"] or config["internlinks"]):
            return 0
        # deny and allow external checking
        if config["denyallow"]:
            for pat, strict in config["externlinks"]:
                if pat.search(self.url):
                    return (1, strict)
            for pat in config["internlinks"]:
                if pat.search(self.url):
                    return 0
            return 0
        else:
            for pat in config["internlinks"]:
                if pat.search(self.url):
                    return 0
            for pat, strict in config["externlinks"]:
                if pat.search(self.url):
                    return (1, strict)
            return (1,0)
        raise ValueError, "internal error in UrlData._getExtern"


    def getContent(self):
        """Precondition: urlConnection is an opened URL."""
        if not self.has_content:
            self.has_content = 1
            t = time.time()
            self.data = self.urlConnection.read()
            self.downloadtime = time.time() - t
            self._init_html_comments()
            debug("DEBUG: comment spans %s\n" % self.html_comments)
        return self.data


    def _init_html_comments(self):
        # if we find an URL inside HTML comments we ignore it
        # so build a list of intervalls which are HTML comments
        index = 0
        while 1:
            match = CommentPatternBegin.search(self.getContent(), index)
            if not match: break
            start = match.start()
            index = match.end() + 1
            end = CommentPatternEnd.search(self.getContent(), index)
            if not match: break
            index = match.end() + 1
            self.html_comments.append((start, match.end()))

    def _isInComment(self, index):
        for low,high in self.html_comments:
            if low < index and index < high:
                return 1
        return 0


    def checkContent(self, warningregex):
        match = warningregex.search(self.getContent())
        if match:
            self.setWarning("Found '"+match.group()+"' in link contents")


    def parseUrl(self, config):
        debug(Config.DebugDelim+"Parsing recursively into\n"+\
              str(self)+"\n"+Config.DebugDelim)
        # search for a possible base reference
        bases = self.searchInForTag(BasePattern)

        baseRef = None
        if len(bases)>=1:
            baseRef = bases[0][0]
            if len(bases)>1:
                self.setWarning("more than one base tag found")

        # search for tags and add found tags to URL queue
        for pattern in LinkPatterns:
            urls = self.searchInForTag(pattern)
            for url,line,name in urls:
                config.appendUrl(GetUrlDataFrom(url,
                        self.recursionLevel+1, self.url, baseRef, line, name))


    def searchInForTag(self, pattern):
        debug("Searching for tag %s, attribute %s" \
	      % (pattern['tag'], pattern['attr']))
        urls = []
        index = 0
        while 1:
            match = pattern['pattern'].search(self.getContent(), index)
            if not match: break
            index = match.end()
            if self._isInComment(match.start()): continue
            # need to strip optional ending quotes for the meta tag
            url = string.strip(StringUtil.stripQuotes(match.group('value')))
            # need to resolve HTML entities
            url = StringUtil.unhtmlify(url)
            lineno=StringUtil.getLineNumber(self.getContent(), match.start())
            # extra feature: get optional name for this bookmark
            name = self.searchInForName(pattern['tag'], pattern['attr'],
	                                match.start(), match.end())
            urls.append((url, lineno, name))
        return urls

    def searchInForName(self, tag, attr, start, end):
        name=""
        if tag=='img':
            all = self.getContent()[start:end]
            mo = re.search("(?i)\s+alt\s*=\s*(?P<name>(\".+?\"|[^\s>]+))", all)
            if mo:
                name = StringUtil.stripQuotes(mo.group('name'))
                name = StringUtil.unhtmlify(name)
        elif tag=='a' and attr=='href':
            all = self.getContent()[end:]
            mo = re.search("(?i)(?P<name>.*?)</a\s*>", all)
            if mo:
                name = mo.group('name')
        return name


    def get_scheme(self):
        return "none"

    def __str__(self):
        return ("%s link\n"
	       "urlname=%s\n"
	       "parentName=%s\n"
	       "baseRef=%s\n"
	       "cached=%s\n"
	       "recursionLevel=%s\n"
	       "urlConnection=%s\n"
	       "line=%s\n"
	       "name=%s" % \
             (self.get_scheme(), self.urlName, self.parentName, self.baseRef,
             self.cached, self.recursionLevel, self.urlConnection, self.line,
	     self.name))


    def _getUserPassword(self, config):
        for rx, user, password in config["authentication"]:
            if rx.match(self.url):
                return user, password
        return None,None


from FileUrlData import FileUrlData
from FindUrlData import FindUrlData
from FtpUrlData import FtpUrlData
from GopherUrlData import GopherUrlData
from HttpUrlData import HttpUrlData
from HttpsUrlData import HttpsUrlData
from JavascriptUrlData import JavascriptUrlData
from MailtoUrlData import MailtoUrlData
from TelnetUrlData import TelnetUrlData
from NntpUrlData import NntpUrlData

def GetUrlDataFrom(urlName, recursionLevel, parentName = None,
                   baseRef = None, line = 0, name = None):
    # search for the absolute url
    url=""
    if urlName and ":" in urlName:
        url = string.lower(urlName)
    elif baseRef and ":" in baseRef:
        url = string.lower(baseRef)
    elif parentName and ":" in parentName:
        url = string.lower(parentName)
    # test scheme
    if re.search("^http:", url):
        return HttpUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    if re.search("^ftp:", url):
        return FtpUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    if re.search("^file:", url):
        return FileUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    if re.search("^telnet:", url):
        return TelnetUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    if re.search("^mailto:", url):
        return MailtoUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    if re.search("^gopher:", url):
        return GopherUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    if re.search("^javascript:", url):
        return JavascriptUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    if re.search("^https:", url):
        return HttpsUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    if re.search("^(s?news|nntp):", url):
        return NntpUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    # Mozillas Technology links start with "find:"
    if re.search("^find:", url):
        return FindUrlData(urlName, recursionLevel, parentName, baseRef, line, name)
    # assume local file
    return FileUrlData(urlName, recursionLevel, parentName, baseRef, line, name)

