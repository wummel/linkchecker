""" linkcheck/Config.py

    Copyright (C) 2000,2001  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

This module stores
* Metadata (version, copyright, author, ...)
* Debug and threading options
* Other configuration options
"""

import ConfigParser, sys, os, re, UserDict, string, time
import Logging, linkcheckerConf
from os.path import expanduser,normpath,normcase,join,isfile
from types import StringType
from urllib import getproxies
from linkcheck import _

Version = linkcheckerConf.version
AppName = linkcheckerConf.name
App = AppName+" "+Version
UserAgent = AppName+"/"+Version
Author =  linkcheckerConf.author
HtmlAuthor = string.replace(Author, ' ', '&nbsp;')
Copyright = "Copyright © 2000,2001 by "+Author
HtmlCopyright = "Copyright &copy; 2000,2001 by "+HtmlAuthor
AppInfo = App+"              "+Copyright
HtmlAppInfo = App+", "+HtmlCopyright
Url = linkcheckerConf.url
Email = linkcheckerConf.author_email
Freeware = AppName+""" comes with ABSOLUTELY NO WARRANTY!
This is free software, and you are welcome to redistribute it
under certain conditions. Look at the file `LICENSE' whithin this
distribution."""
Loggers = {
    "text": Logging.StandardLogger,
    "html": Logging.HtmlLogger,
    "colored": Logging.ColoredLogger,
    "gml": Logging.GMLLogger,
    "sql": Logging.SQLLogger,
    "csv": Logging.CSVLogger,
    "blacklist": Logging.BlacklistLogger,
    "xml": Logging.XMLLogger,
    "test": Logging.TestLogger,
}
# for easy printing: a comma separated logger list
LoggerKeys = reduce(lambda x, y: x+", "+y, Loggers.keys())

# debug options
DebugDelim = "==========================================================\n"
DebugFlag = 0

# note: debugging with more than 1 thread can be painful
def debug(msg):
    if DebugFlag:
        sys.stderr.write(msg)
        sys.stderr.flush()

# path util function
def norm(path):
    return normcase(normpath(expanduser(path)))

# dynamic options
class Configuration(UserDict.UserDict):
    """Dynamic options are stored in this class so you can run
    several checking tasks in one Python interpreter at once
    """

    def __init__(self):
        """Initialize the default options"""
        UserDict.UserDict.__init__(self)
        self.reset()
        # we use this variable to delay the calling of
	# Threader.reduceThreads() because we would call it too often.
        # Therefore we count this variable up to 5 and then we call
        # reduceThreads(). Ok, this is a hack but ItWorksForMe(tm).
        self.reduceCount = 0

    def reset(self):
        """Reset to default values"""
        self['linknumber'] = 0
        self["verbose"] = 0
        self["warnings"] = 0
        self["anchors"] = 0
        self["externlinks"] = []
        self["internlinks"] = []
        self["denyallow"] = 0
        self["authentication"] = [(re.compile(r'^.+'),
	                          'anonymous',
	                          'joe@')]
        self["proxy"] = getproxies()
        self["recursionlevel"] = 1
        self["robotstxt"] = 1
        self["strict"] = 0
        self["fileoutput"] = []
        self["loggingfields"] = "all"
        # Logger configurations
        self["text"] = {
            "filename": "linkchecker-out.txt",
        }
        self['html'] = {
            "filename":        "linkchecker-out.html",
            'colorbackground': '"#fff7e5"',
            'colorurl':        '"#dcd5cf"',
            'colorborder':     '"#000000"',
            'colorlink':       '"#191c83"',
            'tablewarning':    '<td bgcolor="#e0954e">',
            'tableerror':      '<td bgcolor="#db4930">',
            'tableok':         '<td bgcolor="#3ba557">',
        }
        ESC="\x1b"
        self['colored'] = {
            "filename":     "linkchecker-out.ansi",
            'colorparent':  ESC+"[37m",   # white
            'colorurl':     ESC+"[0m",    # standard
            'colorname':    ESC+"[0m",    # standard
            'colorreal':    ESC+"[36m",   # cyan
            'colorbase':    ESC+"[35m",   # magenty
            'colorvalid':   ESC+"[1;32m", # green
            'colorinvalid': ESC+"[1;31m", # red
            'colorinfo':    ESC+"[0m",    # standard
            'colorwarning': ESC+"[1;33m", # yellow
            'colordltime':  ESC+"[0m",    # standard
            'colorreset':   ESC+"[0m",    # reset to standard
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
        self['test'] = {} #  no args for test logger
        # default values
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

    def disableThreading(self):
        """Disable threading by replacing functions with their
        non-threading equivalents
	"""
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
        self.log_newUrl = self.log_newUrl_NoThreads
        self.logLock = None
        self.urls = []
        self.threader = None
        self.dataLock = None

    def enableThreading(self, num):
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
        self.log_newUrl = self.log_newUrl_Threads
        self.logLock = Lock()
        self.urls = Queue.Queue(0)
        self.threader = Threader.Threader(num)
        self.dataLock = Lock()

    def hasMoreUrls_NoThreads(self):
        return len(self.urls)
        
    def finished_NoThreads(self):
        return not self.hasMoreUrls_NoThreads()

    def finish_NoThreads(self):
        pass
        
    def appendUrl_NoThreads(self, url):
        self.urls.append(url)
        
    def getUrl_NoThreads(self):
        return self.urls.pop(0)
        
    def checkUrl_NoThreads(self, url):
        url.check(self)
    
    def urlCache_has_key_NoThreads(self, key):
        return self.urlCache.has_key(key)
        
    def urlCache_get_NoThreads(self, key):
        return self.urlCache[key]
        
    def urlCache_set_NoThreads(self, key, val):
        self.urlCache[key] = val

    def robotsTxtCache_has_key_NoThreads(self, key):
        return self.robotsTxtCache.has_key(key)
        
    def robotsTxtCache_get_NoThreads(self, key):
        return self.robotsTxtCache[key]
        
    def robotsTxtCache_set_NoThreads(self, key, val):
        self.robotsTxtCache[key] = val

    def newLogger(self, name, dict={}):
        namespace = {}
	namespace.update(self[name])
	namespace.update(dict)
        return apply(Loggers[name], (), namespace)

    def incrementLinknumber_NoThreads(self):
        self['linknumber'] += 1
    
    def log_newUrl_NoThreads(self, url):
        if not self["quiet"]: self["log"].newUrl(url)
        for log in self["fileoutput"]:
            log.newUrl(url)

    def log_init(self):
        if not self["quiet"]: self["log"].init()
        for log in self["fileoutput"]:
            log.init()

    def log_endOfOutput(self):
        if not self["quiet"]:
            self["log"].endOfOutput(linknumber=self['linknumber'])
        for log in self["fileoutput"]:
            log.endOfOutput(linknumber=self['linknumber'])

    def incrementLinknumber_Threads(self):
        try:
            self.dataLock.acquire()
            self['linknumber'] += 1
        finally:
            self.dataLock.release()

    def hasMoreUrls_Threads(self):
        return not self.urls.empty()

    def finished_Threads(self):
        time.sleep(0.1)
        if self.reduceCount==5:
            self.reduceCount=0
            self.threader.reduceThreads()
        else:
            self.reduceCount += 1
        return self.threader.finished() and self.urls.empty()

    def finish_Threads(self):
        self.threader.finish()

    def appendUrl_Threads(self, url):
        self.urls.put(url)

    def getUrl_Threads(self):
        return self.urls.get()

    def checkUrl_Threads(self, url):
        self.threader.startThread(url.check, (self,))

    def urlCache_has_key_Threads(self, key):
        try:
            self.urlCacheLock.acquire()
            return self.urlCache.has_key(key)
        finally:
            self.urlCacheLock.release()

    def urlCache_get_Threads(self, key):
        try:
            self.urlCacheLock.acquire()
            return self.urlCache[key]
        finally:
            self.urlCacheLock.release()

    def urlCache_set_Threads(self, key, val):
        try:
            self.urlCacheLock.acquire()
            self.urlCache[key] = val
        finally:
            self.urlCacheLock.release()

    def robotsTxtCache_has_key_Threads(self, key):
        try:
            self.robotsTxtCacheLock.acquire()
            return self.robotsTxtCache.has_key(key)
        finally:
            self.robotsTxtCacheLock.release()

    def robotsTxtCache_get_Threads(self, key):
        try:
            self.robotsTxtCacheLock.acquire()
            return self.robotsTxtCache[key]
        finally:
            self.robotsTxtCacheLock.release()

    def robotsTxtCache_set_Threads(self, key, val):
        try:
            self.robotsTxtCacheLock.acquire()
            self.robotsTxtCache[key] = val
        finally:
            self.robotsTxtCacheLock.release()

    def log_newUrl_Threads(self, url):
        try:
            self.logLock.acquire()
            if not self["quiet"]: self["log"].newUrl(url)
            for log in self["fileoutput"]:
                log.newUrl(url)
        finally:
            self.logLock.release()

    def read(self, files = []):
        if not files:
            # system wide config settings
            config_dir = join(linkcheckerConf.install_data, 'linkchecker')
            files.append(norm(join(config_dir, "linkcheckerrc")))
            # per user config settings
            files.append(norm("~/.linkcheckerrc"))
        self.readConfig(files)

    def warn(self, msg):
        self.message("Config: WARNING: "+msg)

    def error(self, msg):
        self.message("Config: ERROR: "+msg)


    def message(self, msg):
        sys.stderr.write(msg+"\n")
        sys.stderr.flush()


    def readConfig(self, files):
        """this big function reads all the configuration parameters
        used in the linkchecker module."""
        debug("DEBUG: reading configuration from %s\n" % files)
        try:
            cfgparser = ConfigParser.ConfigParser()
            cfgparser.read(files)
        except ConfigParser.Error:
	    return

        section="output"
        try:
            log = cfgparser.get(section, "log")
            if Loggers.has_key(log):
                self['log'] = self.newLogger(log)
            else:
                self.warn(_("invalid log option '%s'") % log)
        except ConfigParser.Error: pass
        try: 
            if cfgparser.getboolean(section, "verbose"):
                self["verbose"] = 1
                self["warnings"] = 1
        except ConfigParser.Error: pass
        try: self["quiet"] = cfgparser.getboolean(section, "quiet")
        except ConfigParser.Error: pass
        try: self["warnings"] = cfgparser.getboolean(section, "warnings")
        except ConfigParser.Error: pass
        try:
            filelist = string.split(cfgparser.get(section, "fileoutput"), ",")
            for arg in filelist:
                arg = string.strip(arg)
                # no file output for the blacklist Logger
                if Loggers.has_key(arg) and arg != "blacklist":
		    self['fileoutput'].append(
                         self.newLogger(arg, {'fileoutput':1}))
	except ConfigParser.Error: pass
        for key in Loggers.keys():
            if cfgparser.has_section(key):
                for opt in cfgparser.options(key):
                    try: self[key][opt] = cfgparser.get(key, opt)
                    except ConfigParser.Error: pass
        try:
            self['loggingfields'] = map(string.strip, string.split(
	        cfgparser.get(section, 'loggingfields'), ","))
	except ConfigParser.Error: pass

        section="checking"
        try:
            num = cfgparser.getint(section, "threads")
            if num<=0:
                self.disableThreads()
            else:
                self.enableThreads(num)
        except ConfigParser.Error: pass
        try: self["anchors"] = cfgparser.getboolean(section, "anchors")
        except ConfigParser.Error: pass
        try:
            num = cfgparser.getint(section, "recursionlevel")
            if num<0:
                self.error(_("illegal recursionlevel number %d") % num)
            self["recursionlevel"] = num
        except ConfigParser.Error: pass
        try: 
            self["robotstxt"] = cfgparser.getboolean(section, 
            "robotstxt")
        except ConfigParser.Error: pass
        try: self["strict"] = cfgparser.getboolean(section, "strict")
        except ConfigParser.Error: pass
        try: 
            self["warningregex"] = re.compile(cfgparser.get(section,
            "warningregex"))
        except ConfigParser.Error: pass
        try:
            self["nntpserver"] = cfgparser.get(section, "nntpserver")
        except ConfigParser.Error: pass

        section = "authentication"
	try:
	    i=1
	    while 1:
                tuple = string.split(cfgparser.get(section, "entry%d" % i))
		if len(tuple)!=3: break
                tuple[0] = re.compile(tuple[0])
                self["authentication"].insert(0, tuple)
                i += 1
        except ConfigParser.Error: pass

        section = "filtering"
        try:
            i=1
            while 1:
                tuple = string.split(cfgparser.get(section, "extern%d" % i))
                if len(tuple)!=2: break
                self["externlinks"].append((re.compile(tuple[0]),
		                                 int(tuple[1])))
                i += 1
        except ConfigParser.Error: pass
        try: self["internlinks"].append(re.compile(cfgparser.get(section, "internlinks")))
        except ConfigParser.Error: pass
        try: self["denyallow"] = cfgparser.getboolean(section, "denyallow")
	except ConfigParser.Error: pass
