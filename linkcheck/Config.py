"""store metadata and options"""
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

import ConfigParser, sys, os, re, UserDict, string, time, Cookie
import _linkchecker_configdata, linkcheck, linkcheck.log
from os.path import expanduser,normpath,normcase,join,isfile
from types import StringType
from urllib import getproxies
from debuglevels import *

Version = _linkchecker_configdata.version
AppName = "LinkChecker"
App = AppName+" "+Version
UserAgent = AppName+"/"+Version
Author =  _linkchecker_configdata.author
HtmlAuthor = Author.replace(' ', '&nbsp;')
Copyright = "Copyright © 2000-2002 "+Author
HtmlCopyright = "Copyright &copy; 2000-2002 "+HtmlAuthor
AppInfo = App+"              "+Copyright
HtmlAppInfo = App+", "+HtmlCopyright
Url = _linkchecker_configdata.url
Email = _linkchecker_configdata.author_email
Freeware = AppName+""" comes with ABSOLUTELY NO WARRANTY!
This is free software, and you are welcome to redistribute it
under certain conditions. Look at the file `LICENSE' within this
distribution."""

# debug options
DebugDelim = "==========================================================\n"
DebugLevel = 0

# note: debugging with more than 1 thread can be painful
def debug (level, *args):
    if DebugLevel > level:
        sys.stderr.write("DEBUG(%d):"%level)
        for arg in args:
            sys.stderr.write(" %s"%str(arg))
        sys.stderr.write("\n")
        sys.stderr.flush()

# path util function
def norm (path):
    return normcase(normpath(expanduser(path)))

def _check_morsel (m, host, path):
    # check domain (if its stored)
    if m["domain"] and not host.endswith(m["domain"]):
        return None
    # check path (if its stored)
    if m["path"] and not path.startswith(m["path"]):
        return None
    # check expiry date (if its stored)
    if m["expires"]:
        debug(BRING_IT_ON, "Cookie expires", m["expires"])
        # XXX
    return m.output(header='').strip()


# dynamic options
class Configuration (UserDict.UserDict):
    """Dynamic options are stored in this class so you can run
    several checking tasks in one Python interpreter at once
    """

    def __init__ (self):
        """Initialize the default options"""
        UserDict.UserDict.__init__(self)
        self.reset()
        # we use "reduceCount" to delay the calling of
	# Threader.reduceThreads() because we would call it too often.
        # Therefore we count this variable up to 5 and then we call
        # reduceThreads(). Ok, this is a hack but ItWorksForMe(tm).
        self.reduceCount = 0

    def reset (self):
        """Reset to default values"""
        self['linknumber'] = 0
        self["verbose"] = 0
        self["warnings"] = 0
        self["anchors"] = 0
        self["externlinks"] = []
        self["internlinks"] = []
        self["denyallow"] = 0
        self["interactive"] = 0
        self["authentication"] = [{'pattern': re.compile(r'^.+'),
	                          'user': 'anonymous',
	                          'password': 'joe@',
				 }]
        self["proxy"] = getproxies()
        self["recursionlevel"] = 1
        self["wait"] = 0
        self["robotstxt"] = 1
        self['cookies'] = 0
        self["strict"] = 0
        self["fileoutput"] = []
        # Logger configurations
        self["text"] = {
            "filename": "linkchecker-out.txt",
        }
        self['html'] = {
            "filename":        "linkchecker-out.html",
            'colorbackground': '#fff7e5',
            'colorurl':        '#dcd5cf',
            'colorborder':     '#000000',
            'colorlink':       '#191c83',
            'tablewarning':    '<td bgcolor=#e0954e>',
            'tableerror':      '<td bgcolor=#db4930>',
            'tableok':         '<td bgcolor=#3ba557>',
        }
        self['colored'] = {
            "filename":     "linkchecker-out.ansi",
            'colorparent':  "37",   # white
            'colorurl':     "0",    # standard
            'colorname':    "0",    # standard
            'colorreal':    "36",   # cyan
            'colorbase':    "35",   # magenty
            'colorvalid':   "1;32", # green
            'colorinvalid': "1;31", # red
            'colorinfo':    "0",    # standard
            'colorwarning': "1;33", # yellow
            'colordltime':  "0",    # standard
            'colorreset':   "0",    # reset to standard
        }
        self['gml'] = {
            "filename":     "linkchecker-out.gml",
        }
        self['sql'] = {
            "filename":     "linkchecker-out.sql",
            'separator': ';',
            'dbname': 'linksdb',
        }
        self['csv'] = {
            "filename":     "linkchecker-out.csv",
            'separator': ';',
        }
        self['blacklist'] = {
            "filename":     "~/.blacklist",
	}
        self['xml'] = {
            "filename":     "linkchecker-out.xml",
        }
        self['log'] = self.newLogger('text')
        self["quiet"] = 0
        self["warningregex"] = None
        self["nntpserver"] = os.environ.get("NNTP_SERVER",None)
        self.urlCache = {}
        self.robotsTxtCache = {}
        try:
            import threading
            self.enableThreading(10)
        except ImportError:
            type, value = sys.exc_info()[:2]
            self.disableThreading()
        self.cookies = {}

    def disableThreading (self):
        """Disable threading by replacing functions with their
        non-threading equivalents
	"""
        debug(HURT_ME_PLENTY, "disable threading")
        self["threads"] = 0
        self.hasMoreUrls = self.hasMoreUrls_NoThreads
        self.finished = self.finished_NoThreads
        self.finish = self.finish_NoThreads
        self.appendUrl = self.appendUrl_NoThreads
        self.getUrl = self.getUrl_NoThreads
        self.checkUrl = self.checkUrl_NoThreads
        self.urlCache_has_key = self.urlCache_has_key_NoThreads
        self.urlCache_get = self.urlCache_get_NoThreads
        self.urlCache_set = self.urlCache_set_NoThreads
        self.urlCacheLock = None
        self.robotsTxtCache_has_key = self.robotsTxtCache_has_key_NoThreads
        self.robotsTxtCache_get = self.robotsTxtCache_get_NoThreads
        self.robotsTxtCache_set = self.robotsTxtCache_set_NoThreads
        self.robotsTxtCacheLock = None
        self.incrementLinknumber = self.incrementLinknumber_NoThreads
        self.getCookies = self.getCookies_NoThreads
        self.storeCookies = self.storeCookies_NoThreads
        self.log_newUrl = self.log_newUrl_NoThreads
        self.logLock = None
        self.urls = []
        self.threader = None
        self.dataLock = None
        sys.setcheckinterval(10)

    def enableThreading (self, num):
        """Enable threading by replacing functions with their
        threading equivalents
	"""
        import Queue,Threader
        from threading import Lock
        self["threads"] = 1
        self.hasMoreUrls = self.hasMoreUrls_Threads
        self.finished = self.finished_Threads
        self.finish = self.finish_Threads
        self.appendUrl = self.appendUrl_Threads
        self.getUrl = self.getUrl_Threads
        self.checkUrl = self.checkUrl_Threads
        self.urlCache_has_key = self.urlCache_has_key_Threads
        self.urlCache_get = self.urlCache_get_Threads
        self.urlCache_set = self.urlCache_set_Threads
        self.urlCacheLock = Lock()
        self.robotsTxtCache_has_key = self.robotsTxtCache_has_key_Threads
        self.robotsTxtCache_get = self.robotsTxtCache_get_Threads
        self.robotsTxtCache_set = self.robotsTxtCache_set_Threads
        self.robotsTxtCacheLock = Lock()
        self.incrementLinknumber = self.incrementLinknumber_Threads
        self.getCookies = self.getCookies_Threads
        self.storeCookies = self.storeCookies_Threads
        self.log_newUrl = self.log_newUrl_Threads
        self.logLock = Lock()
        self.urls = Queue.Queue(0)
        self.threader = Threader.Threader(num)
        self.dataLock = Lock()
        sys.setcheckinterval(20)

    def hasMoreUrls_NoThreads (self):
        return len(self.urls)

    def finished_NoThreads (self):
        return not self.hasMoreUrls_NoThreads()

    def finish_NoThreads (self):
        pass

    def appendUrl_NoThreads (self, url):
        self.urls.append(url)

    def getUrl_NoThreads (self):
        return self.urls.pop(0)

    def checkUrl_NoThreads (self, url):
        url.check()

    def urlCache_has_key_NoThreads (self, key):
        return self.urlCache.has_key(key)

    def urlCache_get_NoThreads (self, key):
        return self.urlCache[key]

    def urlCache_set_NoThreads (self, key, val):
        self.urlCache[key] = val

    def robotsTxtCache_has_key_NoThreads (self, key):
        return self.robotsTxtCache.has_key(key)

    def robotsTxtCache_get_NoThreads (self, key):
        return self.robotsTxtCache[key]

    def robotsTxtCache_set_NoThreads (self, key, val):
        self.robotsTxtCache[key] = val

    def storeCookies_NoThreads (self, headers, host):
        output = []
        for h in headers.getallmatchingheaders("Set-Cookie"):
            output.append(h)
            debug(BRING_IT_ON, "Store Cookie", h)
            c = self.cookies.setdefault(host, Cookie.SimpleCookie())
            c.load(h)
        return output

    def getCookies_NoThreads (self, host, path):
        debug(BRING_IT_ON, "Get Cookie", host, path)
        if not self.cookies.has_key(host):
            return []
        cookievals = []
        for m in self.cookies[host].values():
            val = _check_morsel(m, host, path)
            if val:
                cookievals.append(val)
        return cookievals

    def newLogger (self, logtype, dict={}):
        args = {}
	args.update(self[logtype])
	args.update(dict)
        return apply(linkcheck.log.Loggers[logtype], (), args)

    def addLogger(self, logtype, loggerClass, logargs={}):
        "add a new logger type"
        linkcheck.log.Loggers[logtype] = loggerClass
        self[logtype] = logargs

    def incrementLinknumber_NoThreads (self):
        self['linknumber'] += 1

    def log_newUrl_NoThreads (self, url):
        if not self["quiet"]: self["log"].newUrl(url)
        for log in self["fileoutput"]:
            log.newUrl(url)

    def log_init (self):
        if not self["quiet"]: self["log"].init()
        for log in self["fileoutput"]:
            log.init()

    def log_endOfOutput (self):
        if not self["quiet"]:
            self["log"].endOfOutput(linknumber=self['linknumber'])
        for log in self["fileoutput"]:
            log.endOfOutput(linknumber=self['linknumber'])

    def incrementLinknumber_Threads (self):
        try:
            self.dataLock.acquire()
            self['linknumber'] += 1
        finally:
            self.dataLock.release()

    def hasMoreUrls_Threads (self):
        return not self.urls.empty()

    def finished_Threads (self):
        time.sleep(0.1)
        if self.reduceCount==5:
            self.reduceCount=0
            self.threader.reduceThreads()
        else:
            self.reduceCount += 1
        return self.threader.finished() and self.urls.empty()

    def finish_Threads (self):
        self.threader.finish()

    def appendUrl_Threads (self, url):
        self.urls.put(url)

    def getUrl_Threads (self):
        return self.urls.get()

    def checkUrl_Threads (self, url):
        self.threader.startThread(url.check, ())

    def urlCache_has_key_Threads (self, key):
        ret = None
        try:
            self.urlCacheLock.acquire()
            ret = self.urlCache.has_key(key)
        finally:
            self.urlCacheLock.release()
        return ret

    def urlCache_get_Threads (self, key):
        ret = None
        try:
            self.urlCacheLock.acquire()
            ret = self.urlCache[key]
        finally:
            self.urlCacheLock.release()
        return ret

    def urlCache_set_Threads (self, key, val):
        try:
            self.urlCacheLock.acquire()
            self.urlCache[key] = val
        finally:
            self.urlCacheLock.release()

    def robotsTxtCache_has_key_Threads (self, key):
        ret = None
        try:
            self.robotsTxtCacheLock.acquire()
            ret = self.robotsTxtCache.has_key(key)
        finally:
            self.robotsTxtCacheLock.release()
        return ret

    def robotsTxtCache_get_Threads (self, key):
        ret = None
        try:
            self.robotsTxtCacheLock.acquire()
            ret = self.robotsTxtCache[key]
        finally:
            self.robotsTxtCacheLock.release()
        return ret

    def robotsTxtCache_set_Threads (self, key, val):
        try:
            self.robotsTxtCacheLock.acquire()
            self.robotsTxtCache[key] = val
        finally:
            self.robotsTxtCacheLock.release()

    def log_newUrl_Threads (self, url):
        try:
            self.logLock.acquire()
            if not self["quiet"]: self["log"].newUrl(url)
            for log in self["fileoutput"]:
                log.newUrl(url)
        finally:
            self.logLock.release()

    def storeCookies_Threads (self, headers, host):
        try:
            self.dataLock.acquire()
            return self.storeCookies_NoThreads(headers, host)
        finally:
            self.dataLock.release()

    def getCookies_Threads (self, host, path):
        try:
            self.dataLock.acquire()
            return self.getCookies_NoThreads(host, path)
        finally:
            self.dataLock.release()

    def read (self, files = []):
        cfiles = files[:]
        if not cfiles:
            # system wide config settings
            config_dir = join(_linkchecker_configdata.install_data, 'share/linkchecker')
            cfiles.append(norm(join(config_dir, "linkcheckerrc")))
            # per user config settings
            cfiles.append(norm("~/.linkcheckerrc"))
        self.readConfig(cfiles)

    def warn (self, msg):
        self.message(linkcheck._("Warning: %s")%msg)

    def error (self, msg):
        self.message(linkcheck._("Error: %s")%msg)

    def message (self, msg):
        print >> sys.stderr, msg

    def readConfig (self, files):
        """this big function reads all the configuration parameters
        used in the linkchecker module."""
        debug(BRING_IT_ON, "reading configuration from", files)
        try:
            cfgparser = ConfigParser.ConfigParser()
            cfgparser.read(files)
        except ConfigParser.Error, msg:
            debug(BRING_IT_ON, msg)
	    return

        section="output"
        for key in linkcheck.log.Loggers.keys():
            if cfgparser.has_section(key):
                for opt in cfgparser.options(key):
                    try:
                        self[key][opt] = cfgparser.get(key, opt)
                    except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
                try:
		    self[key]['fields'] = map(string.strip,
		         cfgparser.get(key, 'fields').split(','))
                except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try:
            log = cfgparser.get(section, "log")
            if linkcheck.log.Loggers.has_key(log):
                self['log'] = self.newLogger(log)
            else:
                self.warn(linkcheck._("invalid log option '%s'") % log)
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try: 
            if cfgparser.getboolean(section, "verbose"):
                self["verbose"] = 1
                self["warnings"] = 1
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try: self["quiet"] = cfgparser.getboolean(section, "quiet")
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try: self["warnings"] = cfgparser.getboolean(section, "warnings")
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try:
            filelist = cfgparser.get(section, "fileoutput").split(",")
            for arg in filelist:
                arg = arg.strip()
                # no file output for the blacklist Logger
                if linkcheck.log.Loggers.has_key(arg) and arg != "blacklist":
		    self['fileoutput'].append(
                         self.newLogger(arg, {'fileoutput':1}))
	except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)

        section="checking"
        try:
            num = cfgparser.getint(section, "threads")
            if num<=0:
                self.disableThreading()
            else:
                self.enableThreading(num)
        except ConfigParser.Error: debug(HURT_ME_PLENTY, msg)
        try: self["anchors"] = cfgparser.getboolean(section, "anchors")
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try:
            num = cfgparser.getint(section, "recursionlevel")
            if num<0:
                self.error(linkcheck._("illegal recursionlevel number %d") % num)
            self["recursionlevel"] = num
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try: 
            self["robotstxt"] = cfgparser.getboolean(section, "robotstxt")
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try: self["strict"] = cfgparser.getboolean(section, "strict")
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try:
            warn = cfgparser.get(section, "warningregex")
            if warn:
                self["warningregex"] = re.compile(warn)
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try:
            self["nntpserver"] = cfgparser.get(section, "nntpserver")
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try:
            self["interactive"] = cfgparser.getboolean(section, "interactive")
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)

        section = "authentication"
	try:
	    i=1
	    while 1:
                auth = cfgparser.get(section, "entry%d" % i).split()
		if len(auth)!=3: break
                auth[0] = re.compile(auth[0])
                self["authentication"].insert(0, {'pattern': auth[0],
		                                  'user': auth[1],
						  'password': auth[2]})
                i += 1
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)

        section = "filtering"
        try:
            i=1
            while 1:
                tuple = cfgparser.get(section, "extern%d" % i).split()
                if len(tuple)!=2:
                    sys.stderr.write("extern%d: syntax error %s\n"%(i, tuple))
                    break
                self["externlinks"].append(linkcheck.getLinkPat(tuple[0], strict=int(tuple[1])))
                i += 1
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try: self["internlinks"].append(linkcheck.getLinkPat(cfgparser.get(section, "internlinks")))
        except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
        try: self["denyallow"] = cfgparser.getboolean(section, "denyallow")
	except ConfigParser.Error, msg: debug(HURT_ME_PLENTY, msg)
