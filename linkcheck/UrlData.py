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
try:
    import DNS
except ImportError:
    print >>sys.stderr, "You have to install PyDNS from http://pydns.sf.net/"
    raise SystemExit
DNS.DiscoverNameServers()

import Config, StringUtil, linkcheck, linkname, test_support, timeoutsocket
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
   DNS.Error,
   timeoutsocket.Timeout,
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
    ([^"'>]|"[^"\n]*"|'[^'\n]*')*         # skip leading attributes
    %s             # attrib name
    \s*            # whitespace
    =              # equal sign
    \s*            # whitespace
    (?P<value>     # attribute value
     "[^"\n]*" |   # in double quotes
     '[^'\n]*' |   # in single quotes
     [^\s>]+)      # unquoted
    ([^"'>]|"[^"\n]*"|'[^'\n]*')*         # skip trailing attributes
    >              # close tag
    """


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
    (['meta'],    ['content']),
)

# matcher for <meta http-equiv=refresh> tags
_refresh_re = re.compile(r"(?i)^\d+;\s*url=(?P<url>.+)$")

LinkPatterns = []
for _tags,_attrs in LinkTags:
    _tag = '(%s)'%'|'.join(_tags)
    _attr = '(%s)'%'|'.join(_attrs)
    LinkPatterns.append({'pattern': re.compile(_linkMatcher % (_tag, _attr),
                                               re.VERBOSE),
                         'tags': _tags,
                         'attrs': _attrs})
AnchorPattern = {
    'pattern': re.compile(_linkMatcher % ("a", "name"), re.VERBOSE),
    'tags': ['a'],
    'attrs': ['name'],
}

BasePattern = {
    'pattern': re.compile(_linkMatcher % ("base", "href"), re.VERBOSE),
    'tags': ['base'],
    'attrs': ['href'],
}

#CommentPattern = re.compile("<!--.*?--\s*>", re.DOTALL)
# Workaround for Python 2.0 re module bug
CommentPatternBegin = re.compile(r"<!--")
CommentPatternEnd = re.compile(r"--\s*>")

# regular expression for port numbers
port_re = re.compile(r"\d+")

class UrlData:
    "Representing a URL with additional information like validity etc"

    def __init__ (self,
                  urlName,
                  recursionLevel,
                  config,
                  parentName = None,
                  baseRef = None,
                  line = 0,
		  name = ""):
        self.urlName = urlName
        self.recursionLevel = recursionLevel
        self.config = config
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
        self.extern = (1, 0)
        self.data = None
        self.html_comments = []
        self.has_content = 0
        url = get_absolute_url(self.urlName, self.baseRef, self.parentName)
        # assume file link if no scheme is found
        self.scheme = url.split(":", 1)[0] or "file"

    def setError (self, s):
        self.valid=0
        self.errorString = linkcheck._("Error")+": "+s

    def setValid (self, s):
        self.valid=1
        self.validString = linkcheck._("Valid")+": "+s

    def isHtml (self):
        return 0

    def setWarning (self, s):
        if self.warningString:
            self.warningString += "\n" + s
        else:
            self.warningString = s

    def setInfo (self, s):
        if self.infoString:
            self.infoString += "\n"+s
        else:
            self.infoString = s

    def copyFrom (self, urlData):
        self.errorString = urlData.errorString
        self.validString = urlData.validString
        self.warningString = urlData.warningString
        self.infoString = urlData.infoString
        self.valid = urlData.valid
        self.downloadtime = urlData.downloadtime


    def buildUrl (self):
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
        # check host:port syntax
        host = self.urlTuple[1]
        if ":" in host:
            host,port = host.split(":", 1)
            if not port_re.match(port):
                raise linkcheck.error(linkcheck._("URL has invalid port number"))


    def logMe (self):
        debug(BRING_IT_ON, "logging url")
        self.config.incrementLinknumber()
        if self.config["verbose"] or not self.valid or \
           (self.warningString and self.config["warnings"]):
            self.config.log_newUrl(self)


    def check (self):
        try:
            self._check()
        except KeyboardInterrupt:
            raise
        except (socket.error, select.error):
            # on Unix, ctrl-c can raise
            # error: (4, 'Interrupted system call')
            type, value = sys.exc_info()[:2]
            if type!=4:
                raise
        except test_support.Error:
            raise
        except:
            type, value = sys.exc_info()[:2]
            internal_error()


    def _check (self):
        debug(BRING_IT_ON, "Checking", self)
        if self.recursionLevel and self.config['wait']:
            debug(BRING_IT_ON, "sleeping for", self.config['wait'], "seconds")
            time.sleep(self.config['wait'])
        t = time.time()
        # check syntax
        debug(BRING_IT_ON, "checking syntax")
        if not self.urlName or self.urlName=="":
            self.setError(linkcheck._("URL is null or empty"))
            self.logMe()
            return
        try:
	    self.buildUrl()
            self.extern = self._getExtern()
        except tuple(ExcList):
            type, value, tb = sys.exc_info()
            debug(HURT_ME_PLENTY, "exception",  traceback.format_tb(tb))
            self.setError(str(value))
            self.logMe()
            return

        # check the cache
        debug(BRING_IT_ON, "checking cache")
        if self.config.urlCache_has_key(self.getCacheKey()):
            self.copyFrom(self.config.urlCache_get(self.getCacheKey()))
            self.cached = 1
            self.logMe()
            return

        # apply filter
        debug(BRING_IT_ON, "extern =", self.extern)
        if self.extern[0] and (self.config["strict"] or self.extern[1]):
            self.setWarning(
                  linkcheck._("outside of domain filter, checked only syntax"))
            self.logMe()
            return

        # check connection
        debug(BRING_IT_ON, "checking connection")
        try:
            self.checkConnection()
            if self.urlTuple and self.config["anchors"]:
                self.checkAnchors(self.urlTuple[5])
        except tuple(ExcList):
            type, value, tb = sys.exc_info()
            debug(HURT_ME_PLENTY, "exception",  traceback.format_tb(tb))
            self.setError(str(value))

        # check content
        warningregex = self.config["warningregex"]
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
        if self.allowsRecursion():
            try: self.parseUrl()
            except tuple(ExcList):
                type, value, tb = sys.exc_info()
                debug(HURT_ME_PLENTY, "exception",  traceback.format_tb(tb))
                self.setError(str(value))
        self.closeConnection()
        self.logMe()
        debug(BRING_IT_ON, "caching")
        self.putInCache()


    def closeConnection (self):
        # brute force closing
        if self.urlConnection is not None:
            try: self.urlConnection.close()
            except: pass
            # release variable for garbage collection
            self.urlConnection = None


    def putInCache (self):
        cacheKey = self.getCacheKey()
        if cacheKey and not self.cached:
            self.config.urlCache_set(cacheKey, self)
            self.cached = 1


    def getCacheKey (self):
        if self.urlTuple:
            return urlparse.urlunparse(self.urlTuple)
        return None


    def checkConnection (self):
        self.urlConnection = urllib.urlopen(self.url)


    def allowsRecursion (self):
        return self.valid and \
               self.isHtml() and \
               not self.cached and \
               self.recursionLevel < self.config["recursionlevel"] and \
               not self.extern[0]


    def checkAnchors (self, anchor):
        if not (anchor!="" and self.isHtml() and self.valid):
            return
        self.getContent()
        for cur_anchor,line,name in self.searchInForTag(AnchorPattern):
            if cur_anchor == anchor:
                return
        self.setWarning(linkcheck._("anchor #%s not found") % anchor)


    def _getExtern (self):
        if not (self.config["externlinks"] or self.config["internlinks"]):
            return (0, 0)
        # deny and allow external checking
        Config.debug(HURT_ME_PLENTY, "Url", self.url)
        if self.config["denyallow"]:
            for entry in self.config["externlinks"]:
                Config.debug(HURT_ME_PLENTY, "Extern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (1, entry['strict'])
            for entry in self.config["internlinks"]:
                Config.debug(HURT_ME_PLENTY, "Intern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (1, 0)
            return (0, 0)
        else:
            for entry in self.config["internlinks"]:
                Config.debug(HURT_ME_PLENTY, "Intern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (0, 0)
            for entry in self.config["externlinks"]:
                Config.debug(HURT_ME_PLENTY, "Extern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (1, entry['strict'])
            return (1,0)


    def getContent (self):
        """Precondition: urlConnection is an opened URL."""
        if not self.has_content:
            self.has_content = 1
            t = time.time()
            self.data = self.urlConnection.read()
            self.downloadtime = time.time() - t
            self.init_html_comments()
        return self.data


    def init_html_comments (self):
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


    def is_in_comment (self, index):
        for low,high in self.html_comments:
            if low < index < high:
                return 1
        return 0


    def checkContent (self, warningregex):
        match = warningregex.search(self.getContent())
        if match:
            self.setWarning(linkcheck._("Found %s in link contents") % `match.group()`)


    def parseUrl (self):
        debug(BRING_IT_ON, "Parsing recursively into", self)
        # search for a possible base reference
        bases = self.searchInForTag(BasePattern)

        baseRef = None
        if len(bases)>=1:
            baseRef = bases[0][0]
            if len(bases)>1:
                self.setWarning(linkcheck._("more than one base tag found"))

        # search for tags and add found tags to URL queue
        for pattern in LinkPatterns:
            urls = self.searchInForTag(pattern)
            for url,line,name in urls:
                self.config.appendUrl(GetUrlDataFrom(url,
         self.recursionLevel+1, self.config, self.url, baseRef, line, name))


    def searchInForTag (self, pattern):
        debug(HURT_ME_PLENTY, "Searching for tags", `pattern['tags']`,
	      "attributes", `pattern['attrs']`)
        urls = []
        index = 0
        if 'a' in pattern['tags'] and 'href' in pattern['attrs']:
            tag = 'a'
        elif 'img' in pattern['tags']:
            tag = 'img'
        else:
            tag = ''
        while 1:
            try:
                match = pattern['pattern'].search(self.getContent(), index)
            except RuntimeError, msg:
                self.setError(linkcheck._("""Could not parse HTML content (%s).
You may have a syntax error.
LinkChecker is skipping the remaining content for the link type
<%s %s>.""") % (msg, "|".join(pattern['tags']), "|".join(pattern['attrs'])))
                break
            if not match: break
            index = match.end()
            if self.is_in_comment(match.start()): continue
            # strip quotes
            url = StringUtil.stripQuotes(match.group('value'))
	    if 'meta' in pattern['tags']:
	        metamatch = _refresh_re.match(url)
		if metamatch:
                    url = metamatch.group("url")
		else:
		    # ignore other contents (not for refresh)
		    continue
            # need to resolve HTML entities
            url = StringUtil.unhtmlify(url)
            lineno= StringUtil.getLineNumber(self.getContent(), match.start())
            # extra feature: get optional name for this bookmark
            name = self.searchInForName(tag, match.start(), match.end())
            debug(HURT_ME_PLENTY, "Found", `url`, "name", `name`,
                  "at line", lineno)
            urls.append((url, lineno, name))
        return urls


    def searchInForName (self, tag, start, end):
        name=""
        if tag=='a':
            name = linkname.href_name(self.getContent()[end:])
        elif tag=='img':
            name = linkname.image_name(self.getContent()[start:end])
        return name


    def __str__ (self):
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


    def _getUserPassword (self):
        for auth in self.config["authentication"]:
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


def get_absolute_url (urlName, baseRef, parentName):
    """search for the absolute url"""
    if urlName and ":" in urlName:
        return urlName.lower()
    elif baseRef and ":" in baseRef:
        return baseRef.lower()
    elif parentName and ":" in parentName:
        return parentName.lower()
    return ""


def GetUrlDataFrom (urlName, recursionLevel, config, parentName=None,
                    baseRef=None, line=0, name=None):
    url = get_absolute_url(urlName, baseRef, parentName)
    # test scheme
    if url.startswith("http:"):
        klass = HttpUrlData
    elif url.startswith("ftp:"):
        klass = FtpUrlData
    elif url.startswith("file:"):
        klass = FileUrlData
    elif url.startswith("telnet:"):
        klass = TelnetUrlData
    elif url.startswith("mailto:"):
        klass = MailtoUrlData
    elif url.startswith("gopher:"):
        klass = GopherUrlData
    elif url.startswith("https:"):
        klass = HttpsUrlData
    elif url.startswith("nttp:") or \
         url.startswith("news:") or \
         url.startswith("snews:"):
        klass = NntpUrlData
    # application specific links are ignored
    elif ignored_schemes_re.search(url):
        klass = IgnoredUrlData
    # assume local file
    else:
        klass = FileUrlData
    return klass(urlName, recursionLevel, config, parentName, baseRef, line,
                 name)
