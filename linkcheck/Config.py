""" linkcheck/Config.py

    Copyright (C) 2000  Bastian Kleineidam

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
import Logging, LinkCheckerConf
from os.path import expanduser,normpath,normcase,join,isfile
from types import StringType
from urllib import getproxies
from linkcheck import _

Version = LinkCheckerConf.version
AppName = LinkCheckerConf.name
App = AppName+" "+Version
UserAgent = AppName+"/"+Version
Author =  LinkCheckerConf.author
HtmlAuthor = string.replace(Author, ' ', '&nbsp;')
Copyright = "Copyright © 2000 by "+Author
HtmlCopyright = "Copyright &copy; 2000 by "+HtmlAuthor
AppInfo = App+"              "+Copyright
HtmlAppInfo = App+", "+HtmlCopyright
Url = LinkCheckerConf.url
Email = LinkCheckerConf.author_email
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
        self.reduceCount = 0

    def reset(self):
        """Reset to default values"""
        self.data['linknumber'] = 0
        self.data["verbose"] = 0
        self.data["warnings"] = 0
        self.data["anchors"] = 0
        self.data["externlinks"] = []
        self.data["internlinks"] = []
        self.data["allowdeny"] = 0
        self.data["authentication"] = [(re.compile(r'^.+'),
	                               'anonymous',
	                               'joe@')]
        self.data["proxy"] = getproxies()
        self.data["recursionlevel"] = 1
        self.data["robotstxt"] = 0
        self.data["strict"] = 0
        self.data["fileoutput"] = []
        # Logger configurations
        self.data["text"] = {
            "filename": "linkchecker-out.txt",
        }
        self.data['html'] = {
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
        self.data['colored'] = {
            "filename":     "linkchecker-out.ansi",
            'colorparent':  ESC+"[37m",   # white
            'colorurl':     ESC+"[0m",    # standard
            'colorreal':    ESC+"[36m",   # cyan
            'colorbase':    ESC+"[35m",   # magenty
            'colorvalid':   ESC+"[1;32m", # green
            'colorinvalid': ESC+"[1;31m", # red
            'colorinfo':    ESC+"[0m",    # standard
            'colorwarning': ESC+"[1;33m", # yellow
            'colordltime':  ESC+"[0m",    # standard
            'colorreset':   ESC+"[0m",    # reset to standard
        }
        self.data['gml'] = {
            "filename":     "linkchecker-out.gml",
        }
        self.data['sql'] = {
            "filename":     "linkchecker-out.sql",
            'separator': ';',
            'dbname': 'linksdb',
        }
        self.data['csv'] = {
            "filename":     "linkchecker-out.csv",
            'separator': ';',
        }
        self.data['blacklist'] = {
            "filename":     "~/.blacklist",
	}
        # default values
        self.data['log'] = self.newLogger('text')
        self.data["quiet"] = 0
        self.data["warningregex"] = None
        self.data["nntpserver"] = os.environ.get("NNTP_SERVER",None)
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
        self.data["threads"] = 0
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
        self.data["threads"] = 1
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
	namespace.update(self.data[name])
	namespace.update(dict)
        return apply(Loggers[name], (), namespace)

    def incrementLinknumber_NoThreads(self):
        self.data['linknumber'] = self.data['linknumber'] + 1
    
    def log_newUrl_NoThreads(self, url):
        if not self.data["quiet"]: self.data["log"].newUrl(url)
        for log in self.data["fileoutput"]:
            log.newUrl(url)

    def log_init(self):
        if not self.data["quiet"]: self.data["log"].init()
        for log in self.data["fileoutput"]:
            log.init()

    def log_endOfOutput(self):
        if not self.data["quiet"]:
            self.data["log"].endOfOutput(linknumber=self.data['linknumber'])
        for log in self.data["fileoutput"]:
            log.endOfOutput(linknumber=self.data['linknumber'])

    def incrementLinknumber_Threads(self):
        try:
            self.dataLock.acquire()
            self.data['linknumber'] = self.data['linknumber'] + 1
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
            self.reduceCount = self.reduceCount + 1
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
            if not self.data["quiet"]: self.data["log"].newUrl(url)
            for log in self.data["fileoutput"]:
                log.newUrl(url)
        finally:
            self.logLock.release()

    def read(self, files = []):
        if not files:
            files.insert(0,norm("~/.linkcheckerrc"))
            config_dir = join(LinkCheckerConf.install_data, 'linkchecker')
            files.insert(0,norm(join(config_dir, "linkcheckerrc")))
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
        used in the linkchecker module.
        """
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
                self.data['log'] = self.newLogger(log)
            else:
                self.warn(_("invalid log option '%s'") % log)
        except ConfigParser.Error: pass
        try: 
            if cfgparser.getboolean(section, "verbose"):
                self.data["verbose"] = 1
                self.data["warnings"] = 1
        except ConfigParser.Error: pass
        try: self.data["quiet"] = cfgparser.getboolean(section, "quiet")
        except ConfigParser.Error: pass
        try: self.data["warnings"] = cfgparser.getboolean(section, "warnings")
        except ConfigParser.Error: pass
        try:
            filelist = string.split(cfgparser.get(section, "fileoutput"))
            for arg in filelist:
                # no file output for the blacklist Logger
                if Loggers.has_key(arg) and arg != "blacklist":
		    self.data['fileoutput'].append(
                         self.newLogger(arg, {'fileoutput':1}))
	except ConfigParser.Error: pass
        for key in Loggers.keys():
            if cfgparser.has_section(key):
                for opt in cfgparser.options(key):
                    try: self.data[key][opt] = cfgparser.get(key, opt)
                    except ConfigParser.Error: pass

        section="checking"
        try:
            num = cfgparser.getint(section, "threads")
            if num<=0:
                self.disableThreads()
            else:
                self.enableThreads(num)
        except ConfigParser.Error: pass
        try: self.data["anchors"] = cfgparser.getboolean(section, "anchors")
        except ConfigParser.Error: pass
        try:
            num = cfgparser.getint(section, "recursionlevel")
            if num<0:
                self.error(_("illegal recursionlevel number %d") % num)
            self.data["recursionlevel"] = num
        except ConfigParser.Error: pass
        try: 
            self.data["robotstxt"] = cfgparser.getboolean(section, 
            "robotstxt")
        except ConfigParser.Error: pass
        try: self.data["strict"] = cfgparser.getboolean(section, "strict")
        except ConfigParser.Error: pass
        try: 
            self.data["warningregex"] = re.compile(cfgparser.get(section,
            "warningregex"))
        except ConfigParser.Error: pass
        try:
            self.data["nntpserver"] = cfgparser.get(section, "nntpserver")
        except ConfigParser.Error: pass

        section = "authentication"
	try:
	    i=1
	    while 1:
                tuple = string.split(cfgparser.get(section, "entry"+`i`))
		if len(tuple)!=3: break
                tuple[0] = re.compile(tuple[0])
                self.data["authentication"].append(tuple)
                i = i + 1
        except ConfigParser.Error: pass

        section = "filtering"
        try:
            i=1
            while 1:
                tuple = string.split(cfgparser.get(section, "extern"+`i`))
                if len(tuple)!=2: break
                self.data["externlinks"].append((re.compile(tuple[0]),
		                                 int(tuple[1])))
                i = i + 1
        except ConfigParser.Error: pass
        try: self.data["internlinks"].append(re.compile(cfgparser.get(section, "internlinks")))
        except ConfigParser.Error: pass
        try: self.data["allowdeny"] = cfgparser.getboolean(section, "allowdeny")
	except ConfigParser.Error: pass

