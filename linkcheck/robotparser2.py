""" robotparser.py

    Copyright (C) 2000  Bastian Kleineidam

    You can choose between two licenses when using this package:
    1) GNU GPLv2
    2) PSF license for Python 2.2

    The robots.txt Exclusion Protocol is implemented as specified in
    http://info.webcrawler.com/mak/projects/robots/norobots-rfc.html
"""
import urlparse, urllib, urllib2, httplib, socket, re

__all__ = ["RobotFileParser"]

debug = 0

def _debug (msg):
    if debug: print msg


class RobotFileParser (object):
    """ This class provides a set of methods to read, parse and answer
    questions about a single robots.txt file.

    """
    def __init__ (self, url=''):
        self.set_url(url)
        self._reset()


    def _reset (self):
        self.entries = []
        self.default_entry = None
        self.disallow_all = False
        self.allow_all = False
        self.last_checked = 0


    def mtime (self):
        """Returns the time the robots.txt file was last fetched.

        This is useful for long-running web spiders that need to
        check for new robots.txt files periodically.

        """
        return self.last_checked


    def modified (self):
        """Sets the time the robots.txt file was last fetched to the
        current time.

        """
        import time
        self.last_checked = time.time()


    def set_url (self, url):
        """Sets the URL referring to a robots.txt file."""
        self.url = url
        self.host, self.path = urlparse.urlparse(url)[1:3]


    def read (self):
        """Reads the robots.txt URL and feeds it to the parser."""
        self._reset()
        headers = {'User-Agent': 'Python RobotFileParser/2.0',
                   'Accept-Encoding' : 'gzip;q=1.0, deflate;q=0.9, identity;q=0.5'}
        req = urllib2.Request(self.url, None, headers)
        try:
            f = _opener.open(req)
        except urllib2.HTTPError, x:
            if x.code in (401, 403):
                self.disallow_all = True
                _debug("disallow all")
            else:
                self.allow_all = True
                _debug("allow all")
            return
        except (socket.gaierror, socket.error, urllib2.URLError), x:
            # no network
            self.allow_all = True
            _debug("allow all")
            return
        except IOError, data:
            if data and data[0] == 'http error' and data[1] == 404:
                self.allow_all = True
                _debug("allow all")
            else:
                self.allow_all = True
                _debug("allow all")
            return
        lines = []
        line = f.readline()
        while line:
            lines.append(line.strip())
            line = f.readline()
        _debug("parse lines")
        self.parse(lines)


    def _add_entry (self, entry):
        if "*" in entry.useragents:
            # the default entry is considered last
            self.default_entry = entry
        else:
            self.entries.append(entry)


    def parse (self, lines):
        """parse the input lines from a robot.txt file.
           We allow that a user-agent: line is not preceded by
           one or more blank lines."""
        state = 0
        linenumber = 0
        entry = Entry()

        for line in lines:
            linenumber += 1
            if not line:
                if state==1:
                    _debug("line %d: warning: you should insert"
                           " allow: or disallow: directives below any"
                           " user-agent: line" % linenumber)
                    entry = Entry()
                    state = 0
                elif state==2:
                    self._add_entry(entry)
                    entry = Entry()
                    state = 0
            # remove optional comment and strip line
            i = line.find('#')
            if i>=0:
                line = line[:i]
            line = line.strip()
            if not line:
                continue
            line = line.split(':', 1)
            if len(line) == 2:
                line[0] = line[0].strip().lower()
                line[1] = urllib.unquote(line[1].strip())
                if line[0] == "user-agent":
                    if state==2:
                        _debug("line %d: warning: you should insert a blank"
                               " line before any user-agent"
                               " directive" % linenumber)
                        self._add_entry(entry)
                        entry = Entry()
                    entry.useragents.append(line[1])
                    state = 1
                elif line[0] == "disallow":
                    if state==0:
                        _debug("line %d: error: you must insert a user-agent:"
                               " directive before this line" % linenumber)
                    else:
                        entry.rulelines.append(RuleLine(line[1], 0))
                        state = 2
                elif line[0] == "allow":
                    if state==0:
                        _debug("line %d: error: you must insert a user-agent:"
                               " directive before this line" % linenumber)
                    else:
                        entry.rulelines.append(RuleLine(line[1], 1))
                else:
                    _debug("line %d: warning: unknown key %s" % (linenumber,
                               line[0]))
            else:
                _debug("line %d: error: malformed line %s"%(linenumber, line))
        if state==2:
            self.entries.append(entry)
        _debug("Parsed rules:\n%s" % str(self))


    def can_fetch (self, useragent, url):
        """using the parsed robots.txt decide if useragent can fetch url"""
        _debug("Checking robot.txt allowance for:\n  user agent: %s\n  url: %s" %
               (`useragent`, `url`))
        if self.disallow_all:
            return False
        if self.allow_all:
            return True
        # search for given user agent matches
        # the first match counts
        url = urllib.quote(urlparse.urlparse(urllib.unquote(url))[2]) or "/"
        for entry in self.entries:
            if entry.applies_to(useragent):
                return entry.allowance(url)
        # try the default entry last
        if self.default_entry is not None:
            return self.default_entry.allowance(url)
        # agent not found ==> access granted
        return True


    def __str__ (self):
        lines = [str(entry) for entry in self.entries]
        if self.default_entry is not None:
            lines.append(str(self.default_entry))
        return "\n\n".join(lines)


class RuleLine:
    """A rule line is a single "Allow:" (allowance==1) or "Disallow:"
       (allowance==0) followed by a path."""
    def __init__ (self, path, allowance):
        if path == '' and not allowance:
            # an empty value means allow all
            allowance = True
        self.path = urllib.quote(path)
        self.allowance = allowance


    def applies_to (self, filename):
        return self.path=="*" or filename.startswith(self.path)


    def __str__ (self):
        return (self.allowance and "Allow" or "Disallow")+": "+self.path


class Entry:
    """An entry has one or more user-agents and zero or more rulelines"""
    def __init__ (self):
        self.useragents = []
        self.rulelines = []


    def __str__ (self):
        lines = ["User-agent: %s"%`agent` for agent in self.useragents]
        lines.extend([str(line) for line in self.rulelines])
        return "\n".join(lines)


    def applies_to (self, useragent):
        """check if this entry applies to the specified agent"""
        # split the name token and make it lower case
        if not useragent:
            return True
        useragent = useragent.split("/")[0].lower()
        for agent in self.useragents:
            if agent=='*':
                # we have the catch-all agent
                return True
            agent = agent.lower()
            if useragent in agent:
                return True
        return False


    def allowance (self, filename):
        """Preconditions:
        - our agent applies to this entry
        - filename is URL decoded"""
        for line in self.rulelines:
            _debug((filename, str(line), line.allowance))
            if line.applies_to(filename):
                return line.allowance
        return True

###########################################################################
# urlutils.py - Simplified urllib handling
#
#   Written by Chris Lawrence <lawrencc@debian.org>
#   (C) 1999-2002 Chris Lawrence
#
# This program is freely distributable per the following license:
#
##  Permission to use, copy, modify, and distribute this software and its
##  documentation for any purpose and without fee is hereby granted,
##  provided that the above copyright notice appears in all copies and that
##  both that copyright notice and this permission notice appear in
##  supporting documentation.
##
##  I DISCLAIM ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL
##  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL I
##  BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
##  DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
##  WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
##  ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
##  SOFTWARE.
def decode (page):
    "gunzip or deflate a compressed page"
    encoding = page.info().get("Content-Encoding") 
    if encoding in ('gzip', 'x-gzip', 'deflate'):
        from cStringIO import StringIO
        import zlib, gzip
        # cannot seek in socket descriptors, so must get content now
        content = page.read()
        try:
            if encoding == 'deflate':
                fp = StringIO(zlib.decompress(content))
            else:
                fp = gzip.GzipFile('', 'rb', 9, StringIO(content))
        except zlib.error, msg:
            # XXX warning
            fp = StringIO(content)
        # remove content-encoding header
        headers = {}
        ceheader = re.compile(r"(?i)content-encoding:")
        for h in page.info().keys():
            if not ceheader.match(h):
                headers[h] = page.info()[h]
        page = urllib.addinfourl(fp, headers, page.geturl())
    return page

class HttpWithGzipHandler (urllib2.HTTPHandler):
    "support gzip encoding"
    def http_open (self, req):
        return decode(urllib2.HTTPHandler.http_open(self, req))

if hasattr(httplib, 'HTTPS'):
    class HttpsWithGzipHandler (urllib2.HTTPSHandler):
        "support gzip encoding"
        def http_open (self, req):
            return decode(urllib2.HTTPSHandler.http_open(self, req))


_handlers = [urllib2.ProxyHandler(urllib.getproxies()),
    urllib2.UnknownHandler, HttpWithGzipHandler,
    urllib2.ProxyBasicAuthHandler, urllib2.ProxyDigestAuthHandler,
    urllib2.HTTPDefaultErrorHandler, urllib2.HTTPRedirectHandler,
]
if hasattr(httplib, 'HTTPS'):
    _handlers.append(HttpsWithGzipHandler)

_opener = urllib2.build_opener(*_handlers)

# end of urlutils.py routines
###########################################################################


def _check (a, b):
    if not b:
        ac = "access denied"
    else:
        ac = "access allowed"
    if a!=b:
        print "failed"
    else:
        print "ok (%s)" % ac
    print

def _test ():
    global debug
    rp = RobotFileParser()
    debug = 1

    # robots.txt that exists, gotten to by redirection
    rp.set_url('http://www.musi-cal.com/robots.txt')
    rp.read()

    # test for re.escape
    _check(rp.can_fetch('*', 'http://www.musi-cal.com/'), True)
    # this should match the first rule, which is a disallow
    _check(rp.can_fetch('', 'http://www.musi-cal.com/'), False)
    # various cherry pickers
    _check(rp.can_fetch('CherryPickerSE',
                       'http://www.musi-cal.com/cgi-bin/event-search'
                       '?city=San+Francisco'), False)
    _check(rp.can_fetch('CherryPickerSE/1.0',
                       'http://www.musi-cal.com/cgi-bin/event-search'
                       '?city=San+Francisco'), False)
    _check(rp.can_fetch('CherryPickerSE/1.5',
                       'http://www.musi-cal.com/cgi-bin/event-search'
                       '?city=San+Francisco'), False)
    # case sensitivity
    _check(rp.can_fetch('ExtractorPro', 'http://www.musi-cal.com/blubba'), False)
    _check(rp.can_fetch('extractorpro', 'http://www.musi-cal.com/blubba'), False)
    # substring test
    _check(rp.can_fetch('toolpak/1.1', 'http://www.musi-cal.com/blubba'), False)
    # tests for catch-all * agent
    _check(rp.can_fetch('spam', 'http://www.musi-cal.com/vsearch'), False)
    _check(rp.can_fetch('spam', 'http://www.musi-cal.com/Musician/me'), True)
    _check(rp.can_fetch('spam', 'http://www.musi-cal.com/'), True)
    _check(rp.can_fetch('spam', 'http://www.musi-cal.com/'), True)

    # robots.txt that does not exist
    rp.set_url('http://www.lycos.com/robots.txt')
    rp.read()
    _check(rp.can_fetch('Mozilla', 'http://www.lycos.com/search'), True)

if __name__ == '__main__':
    _test()
