"""Base URL handler"""
# Copyright (C) 2000,2001  Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import sys, re, urlparse, urllib, time, traceback, socket, select
import Config, StringUtil, linkcheck, linkname, test_support
from debuglevels import *
debug = Config.debug

# helper function for internal errors
def internal_error ():
    print >> sys.stderr, linkcheck._("""\n********** Oops, I did it again. *************

You have found an internal error in LinkChecker. Please write a bug report
at http://sourceforge.net/tracker/?func=add&group_id=1913&atid=101913
or send mail to %s and include the following information:
1) The URL or file you are testing
2) Your commandline arguments and/or configuration.
3) The system information below.

If you disclose some information because its too private to you thats ok.
I will try to help you nontheless (but you have to give me *something*
I can work with ;).
""") % Config.Email
    type,value = sys.exc_info()[:2]
    print >> sys.stderr, type, value
    import traceback
    traceback.print_exc()
    print_app_info()
    print >> sys.stderr, linkcheck._("\n******** LinkChecker internal error, bailing out ********")
    sys.exit(1)


def print_app_info ():
    import os
    print >> sys.stderr, linkcheck._("System info:")
    print >> sys.stderr, Config.App
    print >> sys.stderr, "Python %s on %s" % (sys.version, sys.platform)
    for key in ("LC_ALL", "LC_MESSAGES",  "http_proxy", "ftp_proxy"):
        value = os.getenv(key)
        if value is not None:
            print >> sys.stderr, key, "=", `value`


# we catch these exceptions, all other exceptions are internal
# or system errors
ExcList = [
   IOError,
   ValueError, # from httplib.py
   linkcheck.error,
   linkcheck.DNS.Error,
   linkcheck.timeoutsocket.Timeout,
   socket.error,
   select.error,
]

if hasattr(socket, "sslerror"):
    ExcList.append(socket.sslerror)

# regular expression to match an HTML tag with one given attribute
_linkMatcher = r"""
    (?i)           # case insensitive
    <              # open tag
    \s*            # whitespace
    %s             # tag name
    \s+            # whitespace
    ([^"'>]|"[^"]*"|'[^']*')*?         # skip leading attributes
    %s             # attrib name
    \s*            # whitespace
    =              # equal sign
    \s*            # whitespace
    (?P<value>     # attribute value
     "[^"]*" |       # in double quotes
     '[^']*' |       # in single quotes
     [^\s>]+)      # unquoted
    ([^"'>]|"[^"]*"|'[^']*')*          # skip trailing attributes
    >              # close tag
    """


# disable meta tag for now, the modified linkmatcher does not allow it
# (['meta'],    ['url']), # <meta http-equiv='refresh' content='x; url=...'>

# ripped mainly from HTML::Tagset.pm
LinkTags = (
    (['a'],       ['href']),
    (['applet'],  ['archive', 'codebase', 'src']),
    (['area'],    ['href']),
    (['bgsound'], ['src']),
    (['blockquote'], ['cite']),
    (['del'],     ['cite']),
    (['embed'],   ['pluginspage', 'src']),
    (['form'],    ['action']),
    (['frame'],   ['src', 'longdesc']),
    (['head'],    ['profile']),
    (['iframe'],  ['src', 'longdesc']),
    (['ilayer'],  ['background']),
    (['img'],     ['src', 'lowsrc', 'longdesc', 'usemap']),
    (['input'],   ['src', 'usemap']),
    (['ins'],     ['cite']),
    (['isindex'], ['action']),
    (['layer'],   ['background', 'src']),
    (['link'],    ['href']),
    (['object'],  ['classid', 'codebase', 'data', 'archive', 'usemap']),
    (['q'],       ['cite']),
    (['script'],  ['src', 'for']),
    (['body', 'table', 'td', 'th', 'tr'], ['background']),
    (['xmp'],     ['href']),
)

LinkPatterns = []
for tags,attrs in LinkTags:
    attr = '(%s)'%'|'.join(attrs)
    tag = '(%s)'%'|'.join(tags)
    LinkPatterns.append({'pattern': re.compile(_linkMatcher % (tag, attr),
                                               re.VERBOSE|re.DOTALL),
                         'tag': tag,
                         'attr': attr})
AnchorPattern = {
    'pattern': re.compile(_linkMatcher % ("a", "name"), re.VERBOSE|re.DOTALL),
    'tag': 'a',
    'attr': 'name',
}

BasePattern = {
    'pattern': re.compile(_linkMatcher % ("base", "href"), re.VERBOSE),
    'tag': 'base',
    'attr': 'href',
}

#CommentPattern = re.compile("<!--.*?--\s*>", re.DOTALL)
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
        self.errorString = linkcheck._("Error")
        self.validString = linkcheck._("Valid")
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
        url = get_absolute_url(self.urlName, self.baseRef, self.parentName)
        # assume file link if no scheme is found
        self.scheme = url.split(":", 1)[0] or "file"

    def setError(self, s):
        self.valid=0
        self.errorString = linkcheck._("Error")+": "+s

    def setValid(self, s):
        self.valid=1
        self.validString = linkcheck._("Valid")+": "+s

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
        self.urlTuple = (self.urlTuple[0], self.urlTuple[1].lower(),
                         self.urlTuple[2], self.urlTuple[ 3],self.urlTuple[4],
                         self.urlTuple[5])
        self.url = urlparse.urlunparse(self.urlTuple)
        # resolve HTML entities
        self.url = StringUtil.unhtmlify(self.url)


    def logMe(self, config):
        debug(BRING_IT_ON, "logging url")
        config.incrementLinknumber()
        if config["verbose"] or not self.valid or \
           (self.warningString and config["warnings"]):
            config.log_newUrl(self)


    def check(self, config):
        try:
            self._check(config)
        except KeyboardInterrupt:
            pass
        except (socket.error, select.error):
            # on Unix, ctrl-c can raise
            # error: (4, 'Interrupted system call')
            type, value = sys.exc_info()[:2]
            if type!=4:
                raise
        except test_support.Error:
            raise
        except:
            internal_error()


    def _check(self, config):
        debug(BRING_IT_ON, "Checking", self)
        if self.recursionLevel and config['wait']:
            debug(BRING_IT_ON, "sleeping for", config['wait'], "seconds")
            time.sleep(config['wait'])
        t = time.time()
        # check syntax
        debug(BRING_IT_ON, "checking syntax")
        if not self.urlName or self.urlName=="":
            self.setError(linkcheck._("URL is null or empty"))
            self.logMe(config)
            return
        try:
	    self.buildUrl()
            self.extern = self._getExtern(config)
        except tuple(ExcList):
            type, value, tb = sys.exc_info()
            debug(HURT_ME_PLENTY, "exception",  traceback.format_tb(tb))
            self.setError(str(value))
            self.logMe(config)
            return

        # check the cache
        debug(BRING_IT_ON, "checking cache")
        if config.urlCache_has_key(self.getCacheKey()):
            self.copyFrom(config.urlCache_get(self.getCacheKey()))
            self.cached = 1
            self.logMe(config)
            return
        
        # apply filter
        debug(BRING_IT_ON, "extern =", self.extern)
        if self.extern and (config["strict"] or self.extern[1]):
            self.setWarning(
                  linkcheck._("outside of domain filter, checked only syntax"))
            self.logMe(config)
            return

        # check connection
        debug(BRING_IT_ON, "checking connection")
        try:
            self.checkConnection(config)
            if self.urlTuple and config["anchors"]:
                self.checkAnchors(self.urlTuple[5])
        except tuple(ExcList):
            type, value, tb = sys.exc_info()
            debug(HURT_ME_PLENTY, "exception",  traceback.format_tb(tb))
            self.setError(str(value))

        # check content
        warningregex = config["warningregex"]
        if warningregex and self.valid:
            debug(BRING_IT_ON, "checking content")
            try:  self.checkContent(warningregex)
            except tuple(ExcList):
                type, value, tb = sys.exc_info()
                debug(HURT_ME_PLENTY, "exception",  traceback.format_tb(tb))
                self.setError(str(value))

        self.checktime = time.time() - t
        # check recursion
        debug(BRING_IT_ON, "checking recursion")
        if self.allowsRecursion(config):
            try: self.parseUrl(config)
            except tuple(ExcList):
                type, value, tb = sys.exc_info()
                debug(HURT_ME_PLENTY, "exception",  traceback.format_tb(tb))
                self.setError(str(value))
        self.closeConnection()
        self.logMe(config)
        debug(BRING_IT_ON, "caching")
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
        raise linkcheck.error, "internal error in UrlData._getExtern"


    def getContent(self):
        """Precondition: urlConnection is an opened URL."""
        if not self.has_content:
            self.has_content = 1
            t = time.time()
            self.data = self.urlConnection.read()
            self.downloadtime = time.time() - t
            self.init_html_comments()
        return self.data


    def init_html_comments(self):
        # if we find an URL inside HTML comments we ignore it
        # so build a list of intervalls which are HTML comments
        index = 0
        while 1:
            match = CommentPatternBegin.search(self.getContent(), index)
            if not match:
	        break
            start = match.start()
            index = match.end() + 1
            match = CommentPatternEnd.search(self.getContent(), index)
            if not match:
                # hmm, we found no matching comment end.
                # we *dont* ignore links here and break
	        break
            index = match.end() + 1
            self.html_comments.append((start, match.end()))
        debug(NIGHTMARE, "comment spans", self.html_comments)


    def is_in_comment(self, index):
        for low,high in self.html_comments:
            if low < index < high:
                return 1
        return 0


    def checkContent(self, warningregex):
        match = warningregex.search(self.getContent())
        if match:
            self.setWarning("Found '"+match.group()+"' in link contents")


    def parseUrl(self, config):
        debug(BRING_IT_ON, "Parsing recursively into", self)
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
        debug(HURT_ME_PLENTY, "Searching for tag", `pattern['tag']`,
	      "attribute", `pattern['attr']`)
        urls = []
        index = 0
        while 1:
            match = pattern['pattern'].search(self.getContent(), index)
            if not match: break
            index = match.end()
            if self.is_in_comment(match.start()): continue
            # strip quotes
            url = StringUtil.stripQuotes(match.group('value'))
            # need to resolve HTML entities
            url = StringUtil.unhtmlify(url)
            lineno= StringUtil.getLineNumber(self.getContent(), match.start())
            # extra feature: get optional name for this bookmark
            name = self.searchInForName(pattern['tag'], pattern['attr'],
	                                match.start(), match.end())
            debug(HURT_ME_PLENTY, "Found", `url`, "at line", lineno)
            urls.append((url, lineno, name))
        return urls


    def searchInForName(self, tag, attr, start, end):
        name=""
        if tag=='img':
            name = linkname.image_name(self.getContent()[start:end])
        elif tag=='a' and attr=='href':
            name = linkname.href_name(self.getContent()[end:])
        return name


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
             (self.scheme, self.urlName, self.parentName, self.baseRef,
             self.cached, self.recursionLevel, self.urlConnection, self.line,
	     self.name))


    def _getUserPassword(self, config):
        for auth in config["authentication"]:
            if auth['pattern'].match(self.url):
                return auth['user'], auth['password']
        return None,None


from FileUrlData import FileUrlData
from IgnoredUrlData import IgnoredUrlData, ignored_schemes_re
from FtpUrlData import FtpUrlData
from GopherUrlData import GopherUrlData
from HttpUrlData import HttpUrlData
from HttpsUrlData import HttpsUrlData
from MailtoUrlData import MailtoUrlData
from TelnetUrlData import TelnetUrlData
from NntpUrlData import NntpUrlData


def get_absolute_url(urlName, baseRef, parentName):
    """search for the absolute url"""
    if urlName and ":" in urlName:
        return urlName.lower()
    elif baseRef and ":" in baseRef:
        return baseRef.lower()
    elif parentName and ":" in parentName:
        return parentName.lower()
    return ""


def GetUrlDataFrom(urlName, recursionLevel, parentName=None,
                   baseRef=None, line=0, name=None):
    url = get_absolute_url(urlName, baseRef, parentName)
    # test scheme
    if re.search("^http:", url):
        klass = HttpUrlData
    elif re.search("^ftp:", url):
        klass = FtpUrlData
    elif re.search("^file:", url):
        klass = FileUrlData
    elif re.search("^telnet:", url):
        klass = TelnetUrlData
    elif re.search("^mailto:", url):
        klass = MailtoUrlData
    elif re.search("^gopher:", url):
        klass = GopherUrlData
    elif re.search("^https:", url):
        klass = HttpsUrlData
    elif re.search("^(s?news|nntp):", url):
        klass = NntpUrlData
    # application specific links are ignored
    elif ignored_schemes_re.search(url):
        klass = IgnoredUrlData
    # assume local file
    else:
        klass = FileUrlData
    return klass(urlName, recursionLevel, parentName, baseRef, line, name)

