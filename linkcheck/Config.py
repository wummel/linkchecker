# -*- coding: iso-8859-1 -*-
"""store metadata and options"""
# Copyright (C) 2000-2003  Bastian Kleineidam
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
import _linkchecker_configdata, i18n
from linkcheck import getLinkPat
from os.path import expanduser, normpath, normcase, join, isfile
from types import StringType
from urllib import getproxies
from debug import *

Version = _linkchecker_configdata.version
AppName = "LinkChecker"
App = AppName+" "+Version
UserAgent = AppName+"/"+Version
Author =  _linkchecker_configdata.author
HtmlAuthor = Author.replace(' ', '&nbsp;')
Copyright = "Copyright © 2000-2003 "+Author
HtmlCopyright = "Copyright &copy; 2000-2003 "+HtmlAuthor
AppInfo = App+"              "+Copyright
HtmlAppInfo = App+", "+HtmlCopyright
Url = _linkchecker_configdata.url
Email = _linkchecker_configdata.author_email
Freeware = AppName+""" comes with ABSOLUTELY NO WARRANTY!
This is free software, and you are welcome to redistribute it
under certain conditions. Look at the file `LICENSE' within this
distribution."""

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
        self["verbose"] = False
        self["warnings"] = False
        self["anchors"] = False
        self["noanchorcaching"] = False
        self["externlinks"] = []
        self["internlinks"] = []
        self["denyallow"] = False
        self["interactive"] = False
        # on ftp, password is set by Pythons ftplib
        self["authentication"] = [{'pattern': re.compile(r'^.+'),
	                          'user': 'anonymous',
	                          'password': '',
				 }]
        self["proxy"] = getproxies()
        self["recursionlevel"] = 1
        self["wait"] = 0
        self['cookies'] = False
        self["strict"] = False
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
            'tablewarning':    '<td bgcolor="#e0954e">',
            'tableerror':      '<td bgcolor="#db4930">',
            'tableok':         '<td bgcolor="#3ba557">',
        }
        self['colored'] = {
            "filename":     "linkchecker-out.ansi",
            'colorparent':  "white",
            'colorurl':     "default",
            'colorname':    "default",
            'colorreal':    "cyan",
            'colorbase':    "purple",
            'colorvalid':   "bold;green",
            'colorinvalid': "bold;red",
            'colorinfo':    "default",
            'colorwarning': "bold;yellow",
            'colordltime':  "default",
            'colordlsize':  "default",
            'colorreset':   "default",
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
        self["quiet"] = False
        self["warningregex"] = None
        self["warnsizebytes"] = None
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
        self["threads"] = False
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
        debug(HURT_ME_PLENTY, "enable threading with %d threads" % num)
        import Queue,Threader
        from threading import Lock
        self["threads"] = True
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
        from linkcheck.log import Loggers
        return Loggers[logtype](**args)

    def addLogger(self, logtype, loggerClass, logargs={}):
        "add a new logger type"
        from linkcheck.log import Loggers
        Loggers[logtype] = loggerClass
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
            self.reduceCount = 0
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

    def readConfig (self, files):
        """this big function reads all the configuration parameters
        used in the linkchecker module."""
        debug(BRING_IT_ON, "reading configuration from", files)
        from linkcheck.log import Loggers
        try:
            cfgparser = ConfigParser.ConfigParser()
            cfgparser.read(files)
        except ConfigParser.Error, msg:
            debug(BRING_IT_ON, msg)
	    return

        section="output"
        for key in Loggers.keys():
            if cfgparser.has_section(key):
                for opt in cfgparser.options(key):
                    try:
                        self[key][opt] = cfgparser.get(key, opt)
                    except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
                try:
		    self[key]['fields'] = map(string.strip,
		         cfgparser.get(key, 'fields').split(','))
                except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try:
            log = cfgparser.get(section, "log")
            if Loggers.has_key(log):
                self['log'] = self.newLogger(log)
            else:
                warn(i18n._("invalid log option '%s'") % log)
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try: 
            if cfgparser.getboolean(section, "verbose"):
                self["verbose"] = True
                self["warnings"] = True
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try: self["quiet"] = cfgparser.getboolean(section, "quiet")
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try: self["warnings"] = cfgparser.getboolean(section, "warnings")
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try:
            filelist = cfgparser.get(section, "fileoutput").split(",")
            for arg in filelist:
                arg = arg.strip()
                # no file output for the blacklist Logger
                if Loggers.has_key(arg) and arg != "blacklist":
		    self['fileoutput'].append(
                         self.newLogger(arg, {'fileoutput':1}))
	except ConfigParser.Error, msg: debug(NIGHTMARE, msg)

        section="checking"
        try:
            num = cfgparser.getint(section, "threads")
            if num > 0:
                self.enableThreading(num)
            else:
                self.disableThreading()
        except ConfigParser.Error: debug(NIGHTMARE, msg)
        try: self["anchors"] = cfgparser.getboolean(section, "anchors")
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try:
            num = cfgparser.getint(section, "recursionlevel")
            self["recursionlevel"] = num
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try: 
            self["robotstxt"] = cfgparser.getboolean(section, "robotstxt")
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try: self["strict"] = cfgparser.getboolean(section, "strict")
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try:
            wr = cfgparser.get(section, "warningregex")
            if wr:
                self["warningregex"] = re.compile(wr)
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try: self["warnsizebytes"] = int(cfgparser.get(section, "warnsizebytes"))
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try:
            self["nntpserver"] = cfgparser.get(section, "nntpserver")
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try:
            self["interactive"] = cfgparser.getboolean(section, "interactive")
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try:
            self["noanchorcaching"] = cfgparser.getboolean(section, "noanchorcaching")
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)

        section = "authentication"
	try:
	    i = 1
	    while 1:
                auth = cfgparser.get(section, "entry%d" % i).split()
		if len(auth)!=3: break
                auth[0] = re.compile(auth[0])
                self["authentication"].insert(0, {'pattern': auth[0],
		                                  'user': auth[1],
						  'password': auth[2]})
                i += 1
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)

        section = "filtering"
        try:
            i = 1
            while 1:
                tuple = cfgparser.get(section, "extern%d" % i).split()
                if len(tuple)!=2:
                    error(i18n._("extern%d: syntax error %s\n")%(i, tuple))
                    break
                self["externlinks"].append(getLinkPat(tuple[0], strict=int(tuple[1])))
                i += 1
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try: self["internlinks"].append(getLinkPat(cfgparser.get(section, "internlinks")))
        except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
        try: self["denyallow"] = cfgparser.getboolean(section, "denyallow")
	except ConfigParser.Error, msg: debug(NIGHTMARE, msg)
