import ConfigParser,sys,os,re,UserDict,string
from os.path import expanduser,normpath,normcase,join,isfile
import Logging

Version = "1.2.1"
AppName = "LinkChecker"
App = AppName+" "+Version
UserAgent = AppName+"/"+Version
Author =  "Bastian Kleineidam"
HtmlAuthor = "Bastian&nbsp;Kleineidam"
Copyright = "Copyright © 2000 by "+Author
HtmlCopyright = "Copyright &copy; 2000 by "+HtmlAuthor
AppInfo = App+"              "+Copyright
HtmlAppInfo = App+", "+HtmlCopyright
Url = "http://linkchecker.sourceforge.net/"
Email = "calvin@users.sourceforge.net"
Freeware = AppName+""" comes with ABSOLUTELY NO WARRANTY!
This is free software, and you are welcome to redistribute it
under certain conditions. Look at the file `LICENSE' whithin this
distribution."""
Loggers = {"text": Logging.StandardLogger,
           "html": Logging.HtmlLogger,
	   "colored": Logging.ColoredLogger,
	   "gml": Logging.GMLLogger,
	   "sql": Logging.SQLLogger}
LoggerKeys = reduce(lambda x, y: x+", "+y, Loggers.keys())
DebugDelim = "==========================================================\n"
DebugFlag = 0

# note: debugging with more than 1 thread can be painful
def debug(msg):
    if DebugFlag:
        sys.stderr.write(msg)
        sys.stderr.flush()


def _norm(path):
    return normcase(normpath(expanduser(path)))


class Configuration(UserDict.UserDict):
    def __init__(self):
        UserDict.UserDict.__init__(self)
        self.data["log"] = Loggers["text"]()
        self.data["verbose"] = 0
        self.data["warnings"] = 0
        self.data["anchors"] = 0
        self.data["externlinks"] = []
        self.data["internlinks"] = []
        self.data["allowdeny"] = 0
        self.data["authentication"] = []
        self.data["proxy"] = 0
        self.data["proxyport"] = 8080
        self.data["recursionlevel"] = 1
        self.data["robotstxt"] = 0
        self.data["strict"] = 0
        self.data["fileoutput"] = []
        self.data["quiet"] = 0
        self.data["warningregex"] = None
        self.data["nntpserver"] = os.environ.get("NNTP_SERVER",None)
        self.urlCache = {}
        self.robotsTxtCache = {}
        try:
            import threading
            self.enableThreading(5)
        except ImportError:
            type, value = sys.exc_info()[:2]
            self.disableThreading()

    def disableThreading(self):
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
        self.log_newUrl = self.log_newUrl_NoThreads
        self.logLock = None
        self.urls = []
        self.threader = None
        self.connectNntp = self.connectNntp_NoThreads
        self.dataLock = None

    def enableThreading(self, num):
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
        self.log_newUrl = self.log_newUrl_Threads
        self.logLock = Lock()
        self.urls = Queue.Queue(0)
        self.threader = Threader.Threader(num)
        self.connectNntp = self.connectNntp_Threads
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
        
    def log_newUrl_NoThreads(self, url):
        if not self.data["quiet"]: self.data["log"].newUrl(url)
        for log in self.data["fileoutput"]:
            log.newUrl(url)

    def log_init(self):
        if not self.data["quiet"]: self.data["log"].init()
        for log in self.data["fileoutput"]:
            log.init()

    def log_endOfOutput(self):
        if not self.data["quiet"]: self.data["log"].endOfOutput()
        for log in self.data["fileoutput"]:
            log.endOfOutput()

    def connectNntp_NoThreads(self):
        if not self.data.has_key("nntp"):
            self._do_connectNntp()

    def connectNntp_Threads(self):
        if not self.data.has_key("nntp"):
            self.dataLock.acquire()
            self._do_connectNntp()
            self.dataLock.release()

    def _do_connectNntp(self):
        import nntplib
        timeout = 1
        while timeout:
            try:
                self.data["nntp"] = nntplib.NNTP(self.data["nntpserver"])
                timeout = 0
            except nntplib.error_perm:
                value = sys.exc_info()[1]
                self.debug(value)
                if re.compile("^505").search(str(value)):
                    import whrandom,time
                    time.sleep(whrandom.randint(30,60))
                else:
                    raise

    def hasMoreUrls_Threads(self):
        return not self.urls.empty()
        
    def finished_Threads(self):
        self.threader.reduceThreads()
        return not self.hasMoreUrls() and self.threader.finished()

    def finish_Threads(self):
        self.threader.finish()
        
    def appendUrl_Threads(self, url):
        self.urls.put(url)
        
    def getUrl_Threads(self):
        return self.urls.get()
        
    def checkUrl_Threads(self, url):
        self.threader.startThread(url.check, (self,))
        
    def urlCache_has_key_Threads(self, key):
        self.urlCacheLock.acquire()
        ret = self.urlCache.has_key(key)
        self.urlCacheLock.release()
        return ret

    def urlCache_get_Threads(self, key):
        self.urlCacheLock.acquire()
        ret = self.urlCache[key]
        self.urlCacheLock.release()
        return ret
    
    def urlCache_set_Threads(self, key, val):
        self.urlCacheLock.acquire()
        self.urlCache[key] = val
        self.urlCacheLock.release()

    def robotsTxtCache_has_key_Threads(self, key):
        self.robotsTxtCacheLock.acquire()
        ret = self.robotsTxtCache.has_key(key)
        self.robotsTxtCacheLock.release()
        return ret

    def robotsTxtCache_get_Threads(self, key):
        self.robotsTxtCacheLock.acquire()
        ret = self.robotsTxtCache[key]
        self.robotsTxtCacheLock.release()
        return ret
    
    def robotsTxtCache_set_Threads(self, key, val):
        self.robotsTxtCacheLock.acquire()
        self.robotsTxtCache[key] = val
        self.robotsTxtCacheLock.release()

    def log_newUrl_Threads(self, url):
        self.logLock.acquire()
        if not self.data["quiet"]: self.data["log"].newUrl(url)
        for log in self.data["fileoutput"]:
            log.newUrl(url)
        self.logLock.release()
        
    def read(self, files = []):
        if not files:
            files.insert(0,_norm("~/.linkcheckerrc"))
            if sys.platform=="win32":
                if not sys.path[0]:
                    path=os.getcwd()
                else:
                    path=sys.path[0]
            else:
                path="/etc"
            files.insert(0,_norm(join(path, "linkcheckerrc")))
        self.readConfig(files)
    
    def warn(self, msg):
        self.message("Config: WARNING: "+msg)
        
    def error(self, msg):
        self.message("Config: ERROR: "+msg)

    def message(self, msg):
        sys.stderr.write(msg+"\n")
        sys.stderr.flush()
    
    def readConfig(self, files):
        try:
            cfgparser = ConfigParser.ConfigParser()
            cfgparser.read(files)
        except ConfigParser.Error:
	    return
        
        section="output"
        try:
            log = cfgparser.get(section, "log")
            if Loggers.has_key(log):
                self.data["log"] = Loggers[log]()
            else:
                self.warn("invalid log option "+log)
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
                if Loggers.has_key(arg):
		    self.data["fileoutput"].append(Loggers[arg](open("linkchecker-out."+arg, "w")))
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
            self.data["proxy"] = cfgparser.get(section, "proxy")
            self.data["proxyport"] = cfgparser.getint(section, "proxyport")
        except ConfigParser.Error: pass
        try:
            num = cfgparser.getint(section, "recursionlevel")
            if num<0:
                self.error("illegal recursionlevel number: "+`num`)
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
        self.data["authentication"].append((re.compile(".*"), "anonymous", "guest@"))

        section = "filtering"
        try:
            i=1
            while 1:
                tuple = string.split(cfgparser.get(section, "extern"+`i`))
                if len(tuple)!=2: break
                self.data["externlinks"].append((re.compile(tuple[0]),
		                                 int(tuple[1])))
        except ConfigParser.Error: pass
        try: self.data["internlinks"].append(re.compile(cfgparser.get(section, "internlinks")))
        except ConfigParser.Error: pass
        try: self.data["allowdeny"] = cfgparser.getboolean(section, "allowdeny")
	except ConfigParser.Error: pass

