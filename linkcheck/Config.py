# -*- coding: iso-8859-1 -*-
"""store metadata and options"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

import ConfigParser
import sys
import os
import re
import Cookie
import sets
import urllib
import _linkchecker_configdata
import bk.log
import bk.containers
import linkcheck
import linkcheck.Threader
try:
    import threading
except ImportError:
    import dummy_threading as threading

Version = _linkchecker_configdata.version
AppName = "LinkChecker"
App = AppName+" "+Version
Author =  _linkchecker_configdata.author
HtmlAuthor = Author.replace(' ', '&nbsp;')
Copyright = "Copyright © 2000-2004 "+Author
HtmlCopyright = "Copyright &copy; 2000-2004 "+HtmlAuthor
AppInfo = App+"              "+Copyright
HtmlAppInfo = App+", "+HtmlCopyright
Url = _linkchecker_configdata.url
Email = _linkchecker_configdata.author_email
UserAgent = "%s/%s (%s; %s)" % (AppName, Version, Url, Email)
Freeware = AppName+""" comes with ABSOLUTELY NO WARRANTY!
This is free software, and you are welcome to redistribute it
under certain conditions. Look at the file `LICENSE' within this
distribution."""

MAX_URL_CACHE = 30000
MAX_ROBOTS_TXT_CACHE = 5000
MAX_COOKIES_CACHE = 500


# path util function
def norm (path):
    return os.path.normcase(os.path.normpath(os.path.expanduser(path)))


def _check_morsel (m, host, path):
    # check domain (if its stored)
    if m["domain"] and not host.endswith(m["domain"]):
        return None
    # check path (if its stored)
    if m["path"] and not path.startswith(m["path"]):
        return None
    # check expiry date (if its stored)
    if m["expires"]:
        bk.log.debug(linkcheck.LOG_CHECK, "Cookie expires", m["expires"])
        # XXX
    return m.output(header='').strip()


# dynamic options
class Configuration (dict):
    """Dynamic options are stored in this class so you can run
    several checking tasks in one Python interpreter at once
    """

    def __init__ (self):
        """Initialize the default options"""
        super(Configuration, self).__init__()
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
        self["anchorcaching"] = True
        self["externlinks"] = []
        self["internlinks"] = []
        self["denyallow"] = False
        self["interactive"] = False
        # on ftp, password is set by Pythons ftplib
        self["authentication"] = [
            {'pattern': re.compile(r'^.+'),
             'user': 'anonymous',
             'password': '',
            }]
        self["proxy"] = urllib.getproxies()
        self["recursionlevel"] = -1
        self["wait"] = 0
        self['cookies'] = False
        self["strict"] = False
        self["status"] = False
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
            "filename":     "~/.linkchecker_blacklist",
	}
        self['xml'] = {
            "filename":     "linkchecker-out.xml",
        }
        self['none'] = {}
        self['log'] = self.newLogger('text')
        self.logLock = threading.Lock()
        self["quiet"] = False
        self["warningregex"] = None
        self["warnsizebytes"] = None
        self["nntpserver"] = os.environ.get("NNTP_SERVER",None)
        self["threads"] = True
        self.threader = linkcheck.Threader.Threader()
        self.setThreads(10)
        self.urlSeen = sets.Set()
        self.urlSeenLock = threading.Lock()
        self.urlCache = bk.containers.LRU(MAX_URL_CACHE)
        self.urlCacheLock = threading.Lock()
        self.robotsTxtCache = bk.containers.LRU(MAX_ROBOTS_TXT_CACHE)
        self.robotsTxtCacheLock = threading.Lock()
        self.urls = []
        self.urlCounter = 0
        self.urlsLock = threading.Lock()
        # basic data lock (eg for cookies, link numbers etc.)
        self.dataLock = threading.Lock()
        self.cookies = bk.containers.LRU(MAX_COOKIES_CACHE)

    def setThreads (self, num):
        bk.log.debug(linkcheck.LOG_CHECK, "set threading with %d threads"%num)
        self.threader.threads_max = num
        if num>0:
            sys.setcheckinterval(50)
        else:
            sys.setcheckinterval(100)

    def newLogger (self, logtype, dict={}):
        args = {}
	args.update(self[logtype])
	args.update(dict)
        return linkcheck.Loggers[logtype](**args)

    def addLogger(self, logtype, loggerClass, logargs={}):
        "add a new logger type"
        linkcheck.Loggers[logtype] = loggerClass
        self[logtype] = logargs

    def log_init (self):
        if not self["quiet"]: self["log"].init()
        for log in self["fileoutput"]:
            log.init()

    def log_endOfOutput (self):
        if not self["quiet"]:
            self["log"].endOfOutput(linknumber=self['linknumber'])
        for log in self["fileoutput"]:
            log.endOfOutput(linknumber=self['linknumber'])

    def incrementLinknumber (self):
        try:
            self.dataLock.acquire()
            self['linknumber'] += 1
        finally:
            self.dataLock.release()

    def hasMoreUrls (self):
        return self.urls

    def finished (self):
        return self.threader.finished() and not self.urls

    def finish (self):
        self.threader.finish()

    def appendUrl (self, urlData):
        self.urlsLock.acquire()
        try:
            # check syntax
            if not urlData.checkSyntax():
                return
            # check the cache
            if not urlData.checkCache():
                return
            self.urlCounter += 1
            if self.urlCounter==1000:
                self.urlCounter = 0
                self.filterUrlQueue()
            self.urls.append(urlData)
        finally:
            self.urlsLock.release()

    def filterUrlQueue (self):
        """remove already cached urls from queue"""
        # note: url lock must be acquired
        olen = len(self.urls)
        self.urls = [ u for u in self.urls if u.checkCache() ]
        removed = olen - len(self.urls)
        print >>sys.stderr, \
          i18n._("removed %d cached urls from incoming queue")%removed

    def getUrl (self):
        """get first url in queue and return it"""
        self.urlsLock.acquire()
        try:
            u = self.urls[0]
            del self.urls[0]
            return u
        finally:
            self.urlsLock.release()

    def checkUrl (self, url):
        self.threader.start_thread(url.check, ())

    def urlSeen_has_key (self, key):
        self.urlSeenLock.acquire()
        try:
            return key in self.urlSeen
        finally:
            self.urlSeenLock.release()

    def urlSeen_set (self, key):
        self.urlSeenLock.acquire()
        try:
            self.urlSeen.add(key)
        finally:
            self.urlSeenLock.release()

    def urlCache_has_key (self, key):
        self.urlCacheLock.acquire()
        try:
            return key in self.urlCache
        finally:
            self.urlCacheLock.release()

    def urlCache_get (self, key):
        self.urlCacheLock.acquire()
        try:
            return self.urlCache[key]
        finally:
            self.urlCacheLock.release()

    def urlCache_set (self, key, val):
        self.urlCacheLock.acquire()
        try:
            bk.log.debug(linkcheck.LOG_CHECK, "caching", repr(key))
            self.urlCache[key] = val
        finally:
            self.urlCacheLock.release()

    def robotsTxtCache_has_key (self, key):
        self.robotsTxtCacheLock.acquire()
        try:
            return self.robotsTxtCache.has_key(key)
        finally:
            self.robotsTxtCacheLock.release()

    def robotsTxtCache_get (self, key):
        self.robotsTxtCacheLock.acquire()
        try:
            return self.robotsTxtCache[key]
        finally:
            self.robotsTxtCacheLock.release()

    def robotsTxtCache_set (self, key, val):
        self.robotsTxtCacheLock.acquire()
        try:
            self.robotsTxtCache[key] = val
        finally:
            self.robotsTxtCacheLock.release()

    def log_newUrl (self, url):
        self.logLock.acquire()
        try:
            if not self["quiet"]:
                self["log"].newUrl(url)
            for log in self["fileoutput"]:
                log.newUrl(url)
        finally:
            self.logLock.release()

    def storeCookies (self, headers, host):
        self.dataLock.acquire()
        try:
            output = []
            for h in headers.getallmatchingheaders("Set-Cookie"):
                output.append(h)
                bk.log.debug(linkcheck.LOG_CHECK, "Store Cookie", h)
                c = self.cookies.setdefault(host, Cookie.SimpleCookie())
                c.load(h)
            return output
        finally:
            self.dataLock.release()

    def getCookies (self, host, path):
        self.dataLock.acquire()
        try:
            bk.log.debug(linkcheck.LOG_CHECK, "Get Cookie", host, path)
            if not self.cookies.has_key(host):
                return []
            cookievals = []
            for m in self.cookies[host].values():
                val = _check_morsel(m, host, path)
                if val:
                    cookievals.append(val)
            return cookievals
        finally:
            self.dataLock.release()

    def read (self, files = []):
        cfiles = files[:]
        if not cfiles:
            # system wide config settings
            config_dir = os.path.join(_linkchecker_configdata.install_data, 'share/linkchecker')
            cfiles.append(norm(os.path.join(config_dir, "linkcheckerrc")))
            # per user config settings
            cfiles.append(norm("~/.linkcheckerrc"))
        self.readConfig(cfiles)

    def readConfig (self, files):
        """this big function reads all the configuration parameters
        used in the linkchecker module."""
        bk.log.debug(linkcheck.LOG_CHECK, "reading configuration from", files)
        try:
            cfgparser = ConfigParser.ConfigParser()
            cfgparser.read(files)
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
	    return

        section="output"
        for key in linkcheck.Loggers.keys():
            if cfgparser.has_section(key):
                for opt in cfgparser.options(key):
                    try:
                        self[key][opt] = cfgparser.get(key, opt)
                    except ConfigParser.Error, msg:
                        bk.log.debug(linkcheck.LOG_CHECK, msg)
                try:
		    self[key]['fields'] = [f.strip() for f in cfgparser.get(key, 'fields').split(',')]
                except ConfigParser.Error, msg:
                    bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            log = cfgparser.get(section, "log")
            if linkcheck.Loggers.has_key(log):
                self['log'] = self.newLogger(log)
            else:
                warn(i18n._("invalid log option '%s'") % log)
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try: 
            if cfgparser.getboolean(section, "verbose"):
                self["verbose"] = True
                self["warnings"] = True
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["quiet"] = cfgparser.getboolean(section, "quiet")
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["status"] = cfgparser.getboolean(section, "status")
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["warnings"] = cfgparser.getboolean(section, "warnings")
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            filelist = cfgparser.get(section, "fileoutput").split(",")
            for arg in filelist:
                arg = arg.strip()
                # no file output for the blacklist and none Logger
                if linkcheck.Loggers.has_key(arg) and arg not in ["blacklist", "none"]:
		    self['fileoutput'].append(
                         self.newLogger(arg, {'fileoutput':1}))
	except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)

        section="checking"
        try:
            num = cfgparser.getint(section, "threads")
            self.setThreads(num)
        except ConfigParser.Error:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["anchors"] = cfgparser.getboolean(section, "anchors")
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            num = cfgparser.getint(section, "recursionlevel")
            self["recursionlevel"] = num
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["strict"] = cfgparser.getboolean(section, "strict")
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            wr = cfgparser.get(section, "warningregex")
            if wr:
                self["warningregex"] = re.compile(wr)
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["warnsizebytes"] = int(cfgparser.get(section, "warnsizebytes"))
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["nntpserver"] = cfgparser.get(section, "nntpserver")
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["interactive"] = cfgparser.getboolean(section, "interactive")
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["anchorcaching"] = cfgparser.getboolean(section, "anchorcaching")
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)

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
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)

        section = "filtering"
        try:
            i = 1
            while 1:
                ctuple = cfgparser.get(section, "extern%d" % i).split()
                if len(ctuple)!=2:
                    error(i18n._("extern%d: syntax error %s\n")%(i, ctuple))
                    break
                self["externlinks"].append(linkcheck.getLinkPat(ctuple[0], strict=int(ctuple[1])))
                i += 1
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["internlinks"].append(linkcheck.getLinkPat(cfgparser.get(section, "internlinks")))
        except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["denyallow"] = cfgparser.getboolean(section, "denyallow")
	except ConfigParser.Error, msg:
            bk.log.debug(linkcheck.LOG_CHECK, msg)
